from django_filters.views import FilterView
from bhtom_alerts.alerts import get_service_classes
from bhtom_alerts.models import BrokerQuery
from bhtom_alerts.views import BrokerQueryFilter


class BrokerQueryListView(FilterView):
    """
    View that displays all saved ``BrokerQuery`` objects.
    """
    model = BrokerQuery
    template_name = 'bhtom_alerts/brokerquery_list.html'
    filterset_class = BrokerQueryFilter

    def get_context_data(self, *args, **kwargs):
        """
        Adds the brokers available to the TOM to the context dictionary.

        :returns: context
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context['installed_brokers'] = {}
        for broker_name, broker in get_service_classes().items():
            if broker.form:
                context['installed_brokers'][broker_name] = broker
        return context
