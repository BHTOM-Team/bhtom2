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
        """
        Ensures that the form parameters are valid and runs the catalog query.

        :param form: CatalogQueryForm with required parameter`s
        :type form: CatalogQueryForm
        """
        try:
            term = form.cleaned_data['term']
            service = form.cleaned_data['service']
            post_data = {
                'terms': term,
                'harvester': service
            }
            header = {
                "Correlation-ID" : get_guid(),
            }
            response = requests.post(settings.HARVESTER_URL + '/findTargetWithHarvester/', data=post_data, headers=header)
            
            if response.status_code == 200:
                # Extract JSON from the response
                self.target = json.loads(response.text)
            else:
                response.raise_for_status()
        except MissingDataException:
            form.add_error('term', ValidationError('Object not found'))
            return self.form_invalid(form)
        except Exception as e:
            # Handle other exceptions, log the error, etc.
#            form.add_error('term', ValidationError(f'Object not found'))
            sanitized_message = f"Object not found: {str(e)}"
            form.add_error('term', ValidationError(sanitized_message))
            logger.error("Oops something went wrong: " + str(e))
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirects to the ``TargetCreateView``. Appends the target parameters to the URL as query parameters in order to
        autofill the ``TargetCreateForm``, including any additional names returned from the query.
        """
        return reverse('targets:create') + '?' + urlencode(self.target)

