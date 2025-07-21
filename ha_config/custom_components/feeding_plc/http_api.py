import csv
import datetime

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant, callback
import logging
import io


logger = logging.getLogger('feeding_api')


class MoreThenMaxValue(BaseException):
    pass


class RecipeCsvUploadView(HomeAssistantView):
    url = "/api/pool/recipe_csv"
    name = "api:recipe_csv"
    requires_auth = True

    @callback
    async def post(self, request):
        data = await request.json()
        csv_text = data.get("csv")
        if not csv_text:
            return self.json({"error": "No CSV data provided"}, status_code=400)

        results = await load_csv_data(csv_text, request.app["hass"])
        if results.get('error'):
            return self.json(results, status_code=400)
        else:
            return self.json(results)


ENTYTIES = {
    'start_time': 'b{pool}_ust_vremia_nachala_{feeding}',
    'duration': 'b{pool}_ust_dlitelnost_{feeding}',
    'period': 'b{pool}_ust_period_{feeding}',
    'quantity': 'b{pool}_ust_kol_vo_kormlenii_{feeding}'
}


async def load_csv_data(csv_text: str, hass: HomeAssistant) -> dict:
    reader = csv.reader(io.StringIO(csv_text))
    results = []
    headers = None
    for row in reader:
        if not headers:
            headers = row
            diff = set(ENTYTIES) - set(headers)
            if diff:
                return {'error': f'не хватает столбцов `{diff}`', 'result': []}
            continue
        row_data = dict(zip(headers, row))
        pool = row_data.pop('pool')
        feeding = row_data.pop('feeding')
        feeding_result = {
            'pool': pool,
            'feeding': feeding,
        }
        for key, value in row_data.items():
            try:
                if key in ('start_time', 'period'):
                    value = datetime.datetime.strptime(value, '%H:%M:%S').time()
                    value = value.hour * 60 + value.minute
                    domain = 'number'
                elif key == 'duration':
                    value = datetime.datetime.strptime(value, '%H:%M:%S').time()
                    value = value.hour * 3600 + value.minute * 60 + value.second
                    if value > 32000:
                        raise MoreThenMaxValue
                    domain = 'number'
                else:
                    value = int(value)
                    domain = 'number'
                entity_id = f'{domain}.{ENTYTIES[key].format(pool=pool.zfill(2), feeding=feeding)}'
                logger.debug(f'set {entity_id} = {value}')
                await hass.services.async_call(
                    domain, "set_value",
                    {"entity_id": entity_id, "value": value},
                    blocking=True
                )
                feeding_result[key] = value
            except (KeyError, AttributeError, ValueError) as e:
                if 'errors' not in feeding_result:
                    feeding_result['errors'] = []
                feeding_result['errors'].append(f'неверный формат данных `{key}`, `{value}`')
                logger.error(f'Bad format {key} = {value}')
                continue
            except MoreThenMaxValue:
                if 'errors' not in feeding_result:
                    feeding_result['errors'] = []
                feeding_result['errors'].append(f'слишком большое значение `{key}`, `{value}`')
                logger.error(f'Very big value {key} = {value}')
                continue
            except Exception as e:
                if 'errors' not in feeding_result:
                    feeding_result['errors'] = []
                feeding_result['errors'].append(f'неизвестная ошибка записи `{key}`, `{value}`')
                logger.exception(f'Exception {key} = {value}')
                continue
        results.append(feeding_result)
    return {'results': results}
