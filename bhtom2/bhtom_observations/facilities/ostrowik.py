from bhtom_base.bhtom_observations.facility import BaseManualObservationFacility


class Ostrowik(BaseManualObservationFacility):
    name = 'Ostrowik'
    SITES = {
        'Ostrowik': {
            'sitecode': 'ostrowik',
            'latitude': 21.42,
            'longitude': 52.0897,
            'elevation': 200
        }
    }

    def get_form(self, observation_type):
        pass

    def submit_observation(self, observation_payload):
        pass

    def validate_observation(self, observation_payload):
        pass

    def get_terminal_observing_states(self):
        pass

    def get_observing_sites(self):
        return self.SITES

    def cancel_observation(self, observation_id):
        pass

    def get_observation_url(self, observation_id):
        pass

    def all_data_products(self, observation_record):
        return []

