import csv
import datetime
import re

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant, callback
import logging
import io


logger = logging.getLogger('feeding_api')


class MoreThenMaxValue(BaseException):
    pass


class ParametersCsvExportView(HomeAssistantView):
    url = "/api/pool/parameters_csv"
    name = "api:parameters_csv"
    requires_auth = True

    @callback
    async def get(self, request):
        """Export all editable feeding_plc parameters to CSV format"""
        hass = request.app["hass"]
        
        # Collect editable entity data (number and time entities only)
        csv_data = []
        headers = ["entity_id", "value"]

        all_entities = hass.states.async_all()
        
        for entity in all_entities:
            if (
                re.match(r'^number\.b\d\d', entity.entity_id)
                or re.match(r'^number\.sh\d', entity.entity_id)
                # or re.match(r'^switch\.b\d\d', entity.entity_id)
            ) and (
                entity.state not in ('unknown', 'undefined')
            ):
                csv_data.append([entity.entity_id, entity.state])
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(csv_data)
        
        # Return CSV response
        csv_content = output.getvalue()
        output.close()

        filename = f"feeding_plc_parameters_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return web.Response(
            text=csv_content,
            content_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )


class ParametersCsvUploadView(HomeAssistantView):
    url = "/api/pool/parameters_csv_upload"
    name = "api:parameters_csv_upload"
    requires_auth = True

    @callback
    async def post(self, request):
        data = await request.json()
        csv_text = data.get("csv")
        if not csv_text:
            return self.json({"error": "No CSV data provided"}, status_code=400)

        results = await load_parameters_csv_data(csv_text, request.app["hass"])
        if results.get("error"):
            return self.json(results, status_code=400)
        return self.json(results)


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


async def load_parameters_csv_data(csv_text: str, hass: HomeAssistant) -> dict:
    reader = csv.reader(io.StringIO(csv_text))
    results: list[dict] = []
    headers = None

    for row in reader:
        if not row:
            continue

        if headers is None:
            headers = row
            # Allow both with/without header
            if len(headers) >= 2 and headers[0] == "entity_id" and headers[1] == "value":
                continue
            # First row is data
            headers = ["entity_id", "value"]

        if len(row) < 2:
            results.append({"entity_id": row[0] if row else None, "errors": ["not enough columns"]})
            continue

        entity_id = row[0].strip()
        value_raw = row[1].strip()

        item_result: dict = {"entity_id": entity_id, "value": value_raw}
        try:
            if entity_id.startswith("number."):
                value = float(value_raw)
                if value.is_integer():
                    value = int(value)
                await hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": entity_id, "value": value},
                    blocking=True,
                )
            # elif entity_id.startswith("switch."):
            #     if value_raw not in ("on", "off"):
            #         raise ValueError("switch value must be 'on' or 'off'")
            #     service = "turn_on" if value_raw == "on" else "turn_off"
            #     await hass.services.async_call(
            #         "switch",
            #         service,
            #         {"entity_id": entity_id},
            #         blocking=True,
            #     )
            else:
                item_result["errors"] = ["unsupported domain"]
                results.append(item_result)
                continue

            item_result["ok"] = True
            results.append(item_result)
        except Exception as e:
            logger.exception("Failed to set value for entity_id: %s = `%s`", entity_id, value_raw)
            item_result["errors"] = [str(e)]
            results.append(item_result)

    return {"results": results}


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
