from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from bhtom2.brokers.catalina import CRTSBroker
from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from bhtom_base.bhtom_targets.models import Target, TargetName

from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
from bhtom2.external_service.data_source_information import DataSource
from bhtom2.brokers.gaia_alerts import GaiaAlertsBroker

sample_response = """<!DOCTYPE html
	PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
<head>
<title>Positional Cone Search</title>
<META http-equiv="CACHE-CONTROL" CONTENT="NO-CACHE"><script type="text/javascript">document.write('<style type="text/css">.tabber{display:none;}</style>');</script>
<link rel="stylesheet" type="text/css" href="/DataRelease/main-v3.css" />
<link rel="stylesheet" type="text/css" href="/DataRelease/flot/layout.css" />
<link rel="stylesheet" type="text/css" href="/DataRelease/scripts/tabber.css" />
<script src="/DataRelease/flot/jquery.js" type="text/JavaScript"></script>
<script src="/DataRelease/flot/jquery.flot.js" type="text/JavaScript"></script>
<script src="/DataRelease/flot/jquery.flot.selection.js" type="text/JavaScript"></script>
<script src="/DataRelease/flot/jquery.flot.errorbars.js" type="text/JavaScript"></script>
<script src="/DataRelease/scripts/tabber.js" type="text/JavaScript"></script>
<script src="/DataRelease/scripts/pixastic.core.js" type="text/JavaScript"></script>
<script src="/DataRelease/scripts/everything.js" type="text/JavaScript"></script>
<script src="/DataRelease/scripts/brightness.js" type="text/JavaScript"></script>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
</head>
<body link="#E1E10" alink="#ffff00" vlink="#00ffff" bgcolor="#00004f" text="#000000" charset="utf-7">
<center>
    <!-- hr noshade size=1 width="95%" -->
        <table border=0 bgcolor="#c0c0c0" cellpadding=2 cellspacing=2>
        <tr>
            <td bgcolor="#000099">
                <table border=0 width="100%" cellpadding=6 cellspacing=0>
                    <tr align="center" bgcolor="#000099">
                        <td bgcolor="#000099">
                        <font color="#ffffff">
                        Querying region
                        </font>
                        </td>
                    </tr>
		    </table>
		    <table border=1 width="100%" bgcolor="#c0c0c0" cellpadding=6 cellspacing=0>
		    <tr align="center" bgcolor="#000099">
		    <td bgcolor="#000099">
		    <font color="yellow">RA
		    </font>
		    </td>
		    <td bgcolor="#000099">
		    <font color="yellow">Dec
		    </font>
		    </td>
                    <td bgcolor="#000099">
                    <font color="yellow">Radius
                    </font>
                    </td>
		    </tr>
		    <tr align="center" bgcolor="#000099">
		    <td bgcolor="#000099">
		    <font color="yellow">137.97214
		    </font>
		    </td>
		    <td bgcolor="#000099">
		    <font color="yellow">38.29239
		    </font>
		    </td>
                    <td bgcolor="#000099">
                    <font color="yellow">0.002
                    </font>
                    </td>
		    </tr>
		    <tr align="center" bgcolor="#000099">
		    <td bgcolor="#000099">
		    <font color="yellow">09:11:53.31
		    </font>
		    </td>
		    <td bgcolor="#000099">
		    <font color="yellow">38:17:32.6
		    </font>
		    </td>
                    <td bgcolor="#000099">
                    <font color="yellow">0.1'
                    </font>
                    </td>
		    </tr>
		    </table>
		    <table border=0 width="100%" cellpadding=6 cellspacing=0>
		    <tr align="center" bgcolor="#000099">
		    <td bgcolor="#000099">
		    <font color="orange">
		    Please wait!
		    </font>
		    </td>
		    </tr>
                </table>
            </td>
        </tr>
            
        </table>
</center>

</html>
<hr><H3>Photcat DB query</H3>
<hr><h2>Query Results</h2><table bgcolor="#c0c0c0" border><tr><Caption>Master Catalog Frame at Coords:</Caption></tr><tr><th>Frame<th>RA<th>Dec<th>Telescope<th>Size<th>RA Min<th>RA Max<th>Dec Min<th>Dec Max</tr><tr><td>1138040<td> 138.05792<td> 38.1<td> 1<td> 2.8<td> 136.215<td> 139.904<td> 36.6627<td> 39.5224</tr>
</table><br><p><table bgcolor="#c0c0c0" border><tr><Caption>Master Objs in Region</Caption></tr><tr><th>OBJ ID<th>Mag<th>RA<th>Dec<th>Offset (")</tr><tr><td>1138040035002<td>19.654<td>137.971427<td>38.292543<td>   2.09</tr>
</table><br><p>
<table border=1 width=500 bgcolor="#c0c0c0"><tr><Caption>Photometry of Objs:</Caption></tr><tr><th>OBJ ID<th>Mag<th>Magerr<th>RA<th>Dec<th>MJD</tr><tr><td>1138040035002<td>20.50<td>0.36<td>137.9715<td>38.2921<td>53711.37082</tr>
<tr><td>1138040035002<td>20.28<td>0.32<td>137.9714<td>38.2927<td>53711.37908</tr>
<tr><td>1138040035002<td>19.80<td>0.25<td>137.9717<td>38.2926<td>53711.38731</tr>
<tr><td>1138040035002<td>18.97<td>0.16<td>137.9720<td>38.2928<td>53734.34727</tr>
<tr><td>1138040035002<td>19.56<td>0.22<td>137.9712<td>38.2927<td>53734.35663</tr>
<tr><td>1138040035002<td>20.87<td>0.45<td>137.9719<td>38.2918<td>53687.46143</tr>
<tr><td>1138040035002<td>20.44<td>0.38<td>137.9717<td>38.2926<td>53854.23319</tr>
<tr><td>1138040035002<td>19.27<td>0.19<td>137.9717<td>38.2926<td>54089.34858</tr>
<tr><td>1138040035002<td>20.61<td>0.40<td>137.9721<td>38.2926<td>53770.19792</tr>
<tr><td>1138040035002<td>20.28<td>0.33<td>137.9720<td>38.2916<td>53770.20515</tr>
<tr><td>1138040035002<td>19.62<td>0.23<td>137.9721<td>38.2925<td>53770.21961</tr>
<tr><td>1138040035002<td>20.64<td>0.40<td>137.9720<td>38.2926<td>53788.17238</tr>
<tr><td>1138040035002<td>20.04<td>0.29<td>137.9719<td>38.2926<td>53788.17892</tr>
<tr><td>1138040035002<td>21.38<td>0.60<td>137.9724<td>38.2926<td>53741.33048</tr>
<tr><td>1138040035002<td>19.55<td>0.22<td>137.9711<td>38.2920<td>53741.35353</tr>
<tr><td>1138040035002<td>19.79<td>0.25<td>137.9713<td>38.2930<td>53757.28673</tr>
<tr><td>1138040035002<td>20.53<td>0.38<td>137.9715<td>38.2924<td>53757.29377</tr>
<tr><td>1138040035002<td>20.11<td>0.30<td>137.9715<td>38.2924<td>53762.24118</tr>
<tr><td>1138040035002<td>20.23<td>0.32<td>137.9716<td>38.2925<td>53762.25414</tr>
<tr><td>1138040035002<td>20.41<td>0.35<td>137.9722<td>38.2928<td>53798.20243</tr>
<tr><td>1138040035002<td>19.86<td>0.26<td>137.9726<td>38.2924<td>53819.16460</tr>
<tr><td>1138040035002<td>20.25<td>0.33<td>137.9717<td>38.2923<td>53819.17094</tr>
<tr><td>1138040035002<td>20.06<td>0.27<td>137.9715<td>38.2927<td>54059.46140</tr>
<tr><td>1138040035002<td>20.05<td>0.27<td>137.9709<td>38.2923<td>54059.48113</tr>
<tr><td>1138040035002<td>21.00<td>0.46<td>137.9721<td>38.2926<td>54035.46295</tr>
<tr><td>1138040035002<td>18.90<td>0.15<td>137.9718<td>38.2926<td>54035.46946</tr>
<tr><td>1138040035002<td>20.07<td>0.20<td>137.9715<td>38.2926<td>54260.15925</tr>
<tr><td>1138040035002<td>20.14<td>0.29<td>137.9719<td>38.2925<td>54176.18006</tr>
<tr><td>1138040035002<td>20.26<td>0.31<td>137.9718<td>38.2925<td>54176.19769</tr>
<tr><td>1138040035002<td>19.69<td>0.23<td>137.9717<td>38.2929<td>54409.40805</tr>
<tr><td>1138040035002<td>19.75<td>0.23<td>137.9720<td>38.2924<td>54424.42824</tr>
<tr><td>1138040035002<td>19.82<td>0.24<td>137.9720<td>38.2924<td>54424.44787</tr>
<tr><td>1138040035002<td>19.36<td>0.20<td>137.9718<td>38.2923<td>54382.46634</tr>
<tr><td>1138040035002<td>20.09<td>0.29<td>137.9718<td>38.2925<td>54382.48600</tr>
<tr><td>1138040035002<td>20.29<td>0.31<td>137.9714<td>38.2927<td>54557.18182</tr>
<tr><td>1138040035002<td>20.07<td>0.28<td>137.9717<td>38.2927<td>54557.19083</tr>
<tr><td>1138040035002<td>20.45<td>0.35<td>137.9726<td>38.2929<td>54557.20851</tr>
<tr><td>1138040035002<td>20.08<td>0.29<td>137.9723<td>38.2924<td>54566.20558</tr>
<tr><td>1138040035002<td>20.22<td>0.34<td>137.9719<td>38.2924<td>54822.50300</tr>
<tr><td>1138040035002<td>19.77<td>0.27<td>137.9721<td>38.2927<td>54822.51509</tr>
<tr><td>1138040035002<td>19.78<td>0.27<td>137.9718<td>38.2925<td>54822.52110</tr>
<tr><td>1138040035002<td>20.33<td>0.32<td>137.9717<td>38.2927<td>54506.25614</tr>
<tr><td>1138040035002<td>20.15<td>0.29<td>137.9726<td>38.2925<td>54506.26273</tr>
<tr><td>1138040035002<td>20.58<td>0.36<td>137.9721<td>38.2927<td>54506.26931</tr>
<tr><td>1138040035002<td>19.97<td>0.26<td>137.9717<td>38.2925<td>54506.27590</tr>
<tr><td>1138040035002<td>19.59<td>0.22<td>137.9716<td>38.2925<td>54466.55324</tr>
<tr><td>1138040035002<td>20.03<td>0.27<td>137.9720<td>38.2926<td>54478.23505</tr>
<tr><td>1138040035002<td>20.27<td>0.31<td>137.9715<td>38.2926<td>54478.23994</tr>
<tr><td>1138040035002<td>19.95<td>0.26<td>137.9719<td>38.2926<td>54478.24487</tr>
<tr><td>1138040035002<td>20.21<td>0.30<td>137.9712<td>38.2924<td>54496.25982</tr>
<tr><td>1138040035002<td>19.65<td>0.22<td>137.9719<td>38.2928<td>54496.26425</tr>
<tr><td>1138040035002<td>19.80<td>0.24<td>137.9710<td>38.2926<td>54496.26883</tr>
<tr><td>1138040035002<td>19.52<td>0.21<td>137.9717<td>38.2927<td>54496.27461</tr>
<tr><td>1138040035002<td>20.58<td>0.36<td>137.9721<td>38.2929<td>54529.26636</tr>
<tr><td>1138040035002<td>19.60<td>0.22<td>137.9710<td>38.2923<td>54529.27957</tr>
<tr><td>1138040035002<td>19.74<td>0.24<td>137.9713<td>38.2923<td>54534.26077</tr>
<tr><td>1138040035002<td>20.16<td>0.29<td>137.9720<td>38.2928<td>54534.26637</tr>
<tr><td>1138040035002<td>19.98<td>0.26<td>137.9717<td>38.2920<td>54534.27194</tr>
<tr><td>1138040035002<td>19.86<td>0.25<td>137.9723<td>38.2929<td>54549.25766</tr>
<tr><td>1138040035002<td>19.55<td>0.21<td>137.9719<td>38.2927<td>54790.43984</tr>
<tr><td>1138040035002<td>21.06<td>0.47<td>137.9716<td>38.2925<td>54790.44716</tr>
<tr><td>1138040035002<td>20.34<td>0.32<td>137.9716<td>38.2921<td>54790.45441</tr>
<tr><td>1138040035002<td>20.06<td>0.27<td>137.9724<td>38.2926<td>54790.46151</tr>
<tr><td>1138040035002<td>20.40<td>0.33<td>137.9719<td>38.2928<td>54941.19224</tr>
<tr><td>1138040035002<td>19.19<td>0.18<td>137.9717<td>38.2925<td>54941.19888</tr>
<tr><td>1138040035002<td>19.52<td>0.21<td>137.9719<td>38.2929<td>54941.20559</tr>
<tr><td>1138040035002<td>20.14<td>0.29<td>137.9718<td>38.2923<td>54941.21220</tr>
<tr><td>1138040035002<td>19.93<td>0.26<td>137.9717<td>38.2927<td>55182.36064</tr>
<tr><td>1138040035002<td>20.00<td>0.26<td>137.9724<td>38.2927<td>54889.18326</tr>
<tr><td>1138040035002<td>20.01<td>0.26<td>137.9712<td>38.2925<td>54889.19110</tr>
<tr><td>1138040035002<td>20.68<td>0.38<td>137.9721<td>38.2926<td>54889.20677</tr>
<tr><td>1138040035002<td>19.86<td>0.25<td>137.9716<td>38.2927<td>54861.19595</tr>
<tr><td>1138040035002<td>20.15<td>0.29<td>137.9721<td>38.2928<td>54861.21429</tr>
<tr><td>1138040035002<td>19.96<td>0.26<td>137.9724<td>38.2922<td>54861.22350</tr>
<tr><td>1138040035002<td>19.41<td>0.20<td>137.9719<td>38.2928<td>54913.11215</tr>
<tr><td>1138040035002<td>20.20<td>0.29<td>137.9716<td>38.2927<td>54913.12851</tr>
<tr><td>1138040035002<td>19.95<td>0.28<td>137.9720<td>38.2929<td>54965.21127</tr>
<tr><td>1138040035002<td>19.61<td>0.23<td>137.9709<td>38.2927<td>54965.22447</tr>
<tr><td>1138040035002<td>20.33<td>0.35<td>137.9726<td>38.2934<td>54965.23111</tr>
<tr><td>1138040035002<td>20.19<td>0.30<td>137.9724<td>38.2929<td>55151.40907</tr>
<tr><td>1138040035002<td>19.98<td>0.27<td>137.9716<td>38.2923<td>55151.42118</tr>
<tr><td>1138040035002<td>19.94<td>0.27<td>137.9711<td>38.2926<td>55131.44663</tr>
<tr><td>1138040035002<td>20.15<td>0.30<td>137.9717<td>38.2925<td>55131.45515</tr>
<tr><td>1138040035002<td>19.38<td>0.23<td>137.9723<td>38.2927<td>55096.50202</tr>
<tr><td>1138040035002<td>20.47<td>0.36<td>137.9718<td>38.2927<td>55293.29185</tr>
<tr><td>1138040035002<td>19.33<td>0.20<td>137.9714<td>38.2925<td>55241.25285</tr>
<tr><td>1138040035002<td>20.10<td>0.29<td>137.9718<td>38.2925<td>55241.26075</tr>
<tr><td>1138040035002<td>20.03<td>0.28<td>137.9712<td>38.2926<td>55241.26870</tr>
<tr><td>1138040035002<td>20.76<td>0.42<td>137.9715<td>38.2926<td>55241.27658</tr>
<tr><td>1138040035002<td>20.38<td>0.42<td>137.9726<td>38.2935<td>55209.35833</tr>
<tr><td>1138040035002<td>19.87<td>0.27<td>137.9724<td>38.2926<td>55358.16652</tr>
<tr><td>1138040035002<td>20.28<td>0.32<td>137.9718<td>38.2924<td>55269.14820</tr>
<tr><td>1138040035002<td>20.76<td>0.41<td>137.9720<td>38.2929<td>55269.15376</tr>
<tr><td>1138040035002<td>20.41<td>0.34<td>137.9720<td>38.2927<td>55269.15939</tr>
<tr><td>1138040035002<td>19.90<td>0.26<td>137.9717<td>38.2928<td>55269.17086</tr>
<tr><td>1138040035002<td>19.51<td>0.22<td>137.9716<td>38.2921<td>55503.45393</tr>
<tr><td>1138040035002<td>20.62<td>0.39<td>137.9722<td>38.2926<td>55503.46561</tr>
<tr><td>1138040035002<td>20.39<td>0.34<td>137.9717<td>38.2926<td>55503.47140</tr>
<tr><td>1138040035002<td>19.36<td>0.20<td>137.9720<td>38.2923<td>55512.41128</tr>
<tr><td>1138040035002<td>20.14<td>0.31<td>137.9719<td>38.2930<td>55679.22878</tr>
<tr><td>1138040035002<td>20.57<td>0.40<td>137.9719<td>38.2925<td>55679.23445</tr>
<tr><td>1138040035002<td>20.29<td>0.34<td>137.9718<td>38.2928<td>55679.24591</tr>
<tr><td>1138040035002<td>20.54<td>0.31<td>137.9722<td>38.2927<td>55598.24335</tr>
<tr><td>1138040035002<td>20.10<td>0.29<td>137.9719<td>38.2925<td>55617.19885</tr>
<tr><td>1138040035002<td>20.67<td>0.40<td>137.9720<td>38.2928<td>55589.29310</tr>
<tr><td>1138040035002<td>20.54<td>0.37<td>137.9719<td>38.2932<td>55589.29996</tr>
<tr><td>1138040035002<td>19.92<td>0.26<td>137.9720<td>38.2922<td>55589.30704</tr>
<tr><td>1138040035002<td>19.68<td>0.24<td>137.9715<td>38.2924<td>55630.18446</tr>
<tr><td>1138040035002<td>20.08<td>0.30<td>137.9717<td>38.2923<td>55630.19205</tr>
<tr><td>1138040035002<td>20.18<td>0.36<td>137.9722<td>38.2916<td>55693.21913</tr>
<tr><td>1138040035002<td>20.69<td>0.43<td>137.9715<td>38.2925<td>55834.46470</tr>
<tr><td>1138040035002<td>20.25<td>0.26<td>137.9719<td>38.2926<td>55889.44461</tr>
<tr><td>1138040035002<td>20.43<td>0.29<td>137.9722<td>38.2927<td>55889.45277</tr>
<tr><td>1138040035002<td>19.91<td>0.22<td>137.9717<td>38.2927<td>55889.46919</tr>
<tr><td>1138040035002<td>20.28<td>0.32<td>137.9715<td>38.2921<td>55922.33808</tr>
<tr><td>1138040035002<td>20.64<td>0.39<td>137.9718<td>38.2926<td>55922.34482</tr>
<tr><td>1138040035002<td>20.45<td>0.35<td>137.9719<td>38.2927<td>55922.35170</tr>
<tr><td>1138040035002<td>20.04<td>0.28<td>137.9719<td>38.2925<td>55922.35850</tr>
<tr><td>1138040035002<td>20.07<td>0.28<td>137.9720<td>38.2928<td>55928.30480</tr>
<tr><td>1138040035002<td>20.21<td>0.30<td>137.9724<td>38.2923<td>55940.49786</tr>
<tr><td>1138040035002<td>19.43<td>0.21<td>137.9720<td>38.2924<td>55980.20017</tr>
<tr><td>1138040035002<td>20.09<td>0.29<td>137.9718<td>38.2923<td>55980.21478</tr>
<tr><td>1138040035002<td>20.35<td>0.36<td>137.9715<td>38.2926<td>55987.20250</tr>
<tr><td>1138040035002<td>20.62<td>0.39<td>137.9719<td>38.2925<td>56016.14602</tr>
<tr><td>1138040035002<td>19.89<td>0.26<td>137.9724<td>38.2925<td>56016.15300</tr>
<tr><td>1138040035002<td>19.02<td>0.17<td>137.9707<td>38.2921<td>56016.15992</tr>
<tr><td>1138040035002<td>19.71<td>0.24<td>137.9717<td>38.2925<td>56044.24864</tr>
<tr><td>1138040035002<td>19.67<td>0.23<td>137.9721<td>38.2924<td>56069.17672</tr>
<tr><td>1138040035002<td>20.12<td>0.30<td>137.9725<td>38.2924<td>56069.18805</tr>
<tr><td>1138040035002<td>18.72<td>0.15<td>137.9710<td>38.2923<td>56074.18529</tr>
<tr><td>1138040035002<td>19.75<td>0.21<td>137.9723<td>38.2928<td>56238.47924</tr>
<tr><td>1138040035002<td>20.19<td>0.26<td>137.9719<td>38.2923<td>56238.48468</tr>
<tr><td>1138040035002<td>19.72<td>0.20<td>137.9724<td>38.2924<td>56238.49020</tr>
<tr><td>1138040035002<td>20.46<td>0.30<td>137.9721<td>38.2924<td>56238.49572</tr>
<tr><td>1138040035002<td>20.06<td>0.24<td>137.9722<td>38.2927<td>56255.37216</tr>
<tr><td>1138040035002<td>20.36<td>0.33<td>137.9716<td>38.2927<td>56271.36353</tr>
<tr><td>1138040035002<td>21.29<td>0.57<td>137.9726<td>38.2926<td>56271.37161</tr>
<tr><td>1138040035002<td>20.11<td>0.29<td>137.9717<td>38.2925<td>56271.37975</tr>
<tr><td>1138040035002<td>21.26<td>0.56<td>137.9719<td>38.2930<td>56297.29214</tr>
<tr><td>1138040035002<td>20.30<td>0.32<td>137.9719<td>38.2927<td>56297.30077</tr>
<tr><td>1138040035002<td>19.66<td>0.23<td>137.9723<td>38.2926<td>56297.30881</tr>
<tr><td>1138040035002<td>20.29<td>0.32<td>137.9722<td>38.2924<td>56297.31680</tr>
<tr><td>1138040035002<td>20.55<td>0.37<td>137.9718<td>38.2926<td>56305.43025</tr>
<tr><td>1138040035002<td>20.35<td>0.33<td>137.9725<td>38.2929<td>56305.43644</tr>
<tr><td>1138040035002<td>20.38<td>0.34<td>137.9719<td>38.2927<td>56305.44277</tr>
<tr><td>1138040035002<td>20.31<td>0.32<td>137.9718<td>38.2927<td>56305.44901</tr>
<tr><td>1138040035002<td>20.49<td>0.39<td>137.9718<td>38.2925<td>56313.39587</tr>
<tr><td>1138040035002<td>18.58<td>0.15<td>137.9721<td>38.2922<td>56323.49791</tr>
<tr><td>1138040035002<td>19.93<td>0.23<td>137.9719<td>38.2925<td>56334.28135</tr>
<tr><td>1138040035002<td>19.93<td>0.23<td>137.9716<td>38.2926<td>56334.28629</tr>
<tr><td>1138040035002<td>19.54<td>0.19<td>137.9719<td>38.2927<td>56334.29198</tr>
<tr><td>1138040035002<td>19.75<td>0.21<td>137.9718<td>38.2926<td>56334.29764</tr>
<tr><td>1138040035002<td>19.28<td>0.17<td>137.9717<td>38.2927<td>56341.25733</tr>
<tr><td>1138040035002<td>21.31<td>0.48<td>137.9725<td>38.2926<td>56341.26362</tr>
<tr><td>1138040035002<td>20.05<td>0.24<td>137.9722<td>38.2922<td>56341.26998</tr>
<tr><td>1138040035002<td>20.17<td>0.25<td>137.9718<td>38.2927<td>56341.27628</tr>
<tr><td>1138040035002<td>19.52<td>0.22<td>137.9717<td>38.2924<td>56356.19542</tr>
<tr><td>1138040035002<td>19.78<td>0.25<td>137.9720<td>38.2926<td>56356.20450</tr>
<tr><td>1138040035002<td>19.64<td>0.23<td>137.9714<td>38.2922<td>56356.21357</tr>
<tr><td>1138040035002<td>20.09<td>0.30<td>137.9717<td>38.2925<td>56356.22297</tr>
<tr><td>1138040035002<td>19.48<td>0.22<td>137.9721<td>38.2925<td>56367.37100</tr>
<tr><td>1138040035002<td>19.73<td>0.25<td>137.9718<td>38.2925<td>56367.37615</tr>
<tr><td>1138040035002<td>19.67<td>0.23<td>137.9715<td>38.2927<td>55947.19932</tr>
<tr><td>1138040035002<td>19.93<td>0.27<td>137.9722<td>38.2928<td>55947.20956</tr>
<tr><td>1138040035002<td>19.77<td>0.21<td>137.9725<td>38.2925<td>55955.26433</tr>
<tr><td>1138040035002<td>20.27<td>0.27<td>137.9717<td>38.2920<td>55955.27793</tr>
<tr><td>1138040035002<td>21.42<td>0.50<td>137.9718<td>38.2941<td>55955.27793</tr>
<tr><td>1138040035002<td>20.31<td>0.27<td>137.9725<td>38.2926<td>55955.28470</tr>
<tr><td>1138040035002<td>19.46<td>0.18<td>137.9720<td>38.2922<td>56404.19051</tr>
<tr><td>1138040035002<td>20.34<td>0.29<td>137.9721<td>38.2928<td>56404.20001</tr>
<tr><td>1138040035002<td>19.83<td>0.33<td>137.9722<td>38.2919<td>56416.14667</tr>
<tr><td>1138040035002<td>19.72<td>0.25<td>137.9720<td>38.2925<td>56432.18649</tr>
</table><br><p>
<p><br><p></HTML>"""

def create_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21edy",
        ra=Decimal(295.16969),
        dec=Decimal(14.58495),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save()
    TargetName.objects.create(target=target, source_name=DataSource.GAIA.name, name='Gaia21edy')

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21een",
        ra=Decimal(113.25287),
        dec=Decimal(-31.98319),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(names={DataSource.GAIA.name: "Gaia21een"})

    return target


class CRTSLightcurveUpdateTestCase(TestCase):
    
    @patch('bhtom2.brokers.catalina.query_external_service',
           return_value=sample_response)
    def test_dont_update_lightcurve_when_no_gaia_name(self, _):

        crts_broker: CRTSBroker = CRTSBroker()

        target: Target = Target(
            name="Gaia21een",
            ra=Decimal(113.25287),
            dec=Decimal(-31.98319),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = crts_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 172)
        self.assertEqual(report.new_points, 172)

    