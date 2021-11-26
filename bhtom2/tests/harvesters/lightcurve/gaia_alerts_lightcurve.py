@patch('bhtom2.harvesters.gaia_alerts_harvester.query_external_service',
       return_value=sample_lightcurve_three_correct_lines)
@patch('bhtom2.harvesters.gaia_alerts_harvester.refresh_reduced_data_view')
def test_update_lightcurve(self, _, mocked_refresh):
    target: Target = Target(
        name="Gaia21edy",
        ra=Decimal(295.16969),
        dec=Decimal(14.58495),
        type='SIDEREAL',
        epoch=2000,
    )

    target.gaia_alert_name = "Gaia21edy"

    update_gaia_lc(target)

    rd: ReducedDatum = ReducedDatum.objects.all()[0]
    rded: ReducedDatumExtraData = ReducedDatumExtraData.objects.all()[0]

    self.assertEqual(rd.value, json.dumps({
        'magnitude': 18.91,
        'filter': 'G_Gaia',
        'error': 0,
        'jd': 2456961.56970
    }))
    self.assertEqual(rd.data_type, 'photometry')
    self.assertEqual(rd.target, target)

    self.assertEqual(rded.reduced_datum, rd)

    extra_data = json.loads(rded.extra_data)

    self.assertEqual(extra_data["facility"], "Gaia")
    self.assertEqual(extra_data["owner"], "Gaia")

    self.assertTrue(mocked_refresh.called)