from django.views.generic.edit import FormView
from django.urls import reverse
from urllib.parse import urlencode
from django.core.exceptions import ValidationError
import requests
from django.conf import settings
import json
from django_guid import get_guid

from .forms import CatalogQueryForm
from bhtom_base.bhtom_catalogs.harvester import MissingDataException
from ..utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_catalogs.views')


class CatalogQueryView(FormView):
    """
    View for querying a specific catalog.
    """

    form_class = CatalogQueryForm
    template_name = 'bhtom_catalogs/query_form.html'
    

    def form_valid(self, form):
        try:
            term = form.cleaned_data['term']
            service = form.cleaned_data['service']
            post_data = {'terms': term, 'harvester': service}
            header = {"Correlation-ID": get_guid()}

            response = requests.post(
                settings.HARVESTER_URL + '/findTargetWithHarvester/',
                data=post_data,
                headers=header,
                timeout=30,
            )

            if response.status_code == 200:
                self.target = response.json()
                if 'discovery_date' not in self.target or self.target.get('discovery_date') is None:
                    self.target['discovery_date'] = ''
                return super().form_valid(form)

            response_text = response.text or ''
            logger.error(
                f'Harvester request failed. status={response.status_code}, '
                f'service={service}, term={term}, response={response_text}'
            )

            if response.status_code == 400 and 'Target not found' in response_text:
                form.add_error('term', ValidationError(f'Object not found dupa {term}'))
            else:
                form.add_error('term', ValidationError(f'Harvester error {response.status_code}: {response_text}'))
            return self.form_invalid(form)

        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f'Invalid JSON from harvester: {e}')
            form.add_error('term', ValidationError('Error while searching for target'))
            return self.form_invalid(form)

        except requests.RequestException as e:
            logger.error(f'Harvester HTTP error: {e}')
            form.add_error('term', ValidationError('Error while searching for target'))
            return self.form_invalid(form)

        except Exception as e:
            logger.error("Oops something went wrong: " + str(e))
            form.add_error('term', ValidationError(f'Error while searching for target: {e}'))
            return self.form_invalid(form)

    def get_success_url(self):
        """
        Redirects to the ``TargetCreateView``. Appends the target parameters to the URL as query parameters in order to
        autofill the ``TargetCreateForm``, including any additional names returned from the query.
        """
        filtered_target = {
            k: str(v) for k, v in self.target.items() if v not in [None, '', 'None']
        }
        return reverse('targets:create') + '?' + urlencode(filtered_target)
