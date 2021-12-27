from typing import Dict

from django.test import SimpleTestCase

from bhtom2.utils.observation_data_extra_data_utils import ObservationDatapointExtraData, decode_datapoint_extra_data


class DecodeDictExtraDataTestCase(SimpleTestCase):
    def test_decode_complete_extra_data(self):
        comment_dict: Dict[str, str] = {
            'facility': 'FacilityName',
            'observation_time': '01-01-2021',
            'owner': 'OwnerName'
        }

        observation_data_extra: ObservationDatapointExtraData = decode_datapoint_extra_data(comment_dict)

        self.assertEqual(observation_data_extra.facility_name, 'FacilityName')
        self.assertEqual(observation_data_extra.observation_time, '01-01-2021')
        self.assertEqual(observation_data_extra.owner, 'OwnerName')
        self.assertEqual(observation_data_extra.to_json_str(), '{"facility": "FacilityName", "observation_time": '
                                                               '"01-01-2021", "owner": "OwnerName"}')

    def test_decode_incomplete_extra_data(self):
        comment_dict: Dict[str, str] = {
            'facility': 'FacilityName',
        }

        observation_data_extra: ObservationDatapointExtraData = decode_datapoint_extra_data(comment_dict)

        self.assertEqual(observation_data_extra.facility_name, 'FacilityName')
        self.assertEqual(observation_data_extra.observation_time, None)
        self.assertEqual(observation_data_extra.owner, None)
        self.assertEqual(observation_data_extra.to_json_str(), '{"facility": "FacilityName"}')
