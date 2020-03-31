
Python example (omfDemo folder) to send OSIsoft Message Format messages to
- OSIsoft Cloud Services
- Edge Data Store
- PI Server via PI Web API or PI Connector Relay.

Postman example to show steps required to setup OMF ingress

Includes two files
1. Postman collection
2. Postman environment to be used with the collection

Load the collection, associated environment file and review collection documentation.
Values that need to be updated in environment file are listed in the table below.
<p>
<table border=0 cellpadding=0 cellspacing=0 width=579 style='border-collapse:
 collapse;table-layout:fixed;width:435pt'>
 <col width=150 style='mso-width-source:userset;mso-width-alt:5347;width:113pt'>
 <col width=281 style='mso-width-source:userset;mso-width-alt:9984;width:211pt'>
 <col width=148 style='mso-width-source:userset;mso-width-alt:5262;width:111pt'>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 width=150 style='height:14.4pt;width:113pt'>environment
  variable</td>
  <td class=xl1523697 width=281 style='width:211pt'>description</td>
  <td class=xl1523697 width=148 style='width:111pt'>example</td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>tenant site name</td>
  <td class=xl1523697></td>
  <td class=xl6523697><a href="https://site.pi.com/">https://site.pi.com</a></td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>tenantid</td>
  <td class=xl1523697></td>
  <td class=xl6523697></td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>namespace</td>
  <td class=xl1523697>name of new or existing namespace</td>
  <td class=xl1523697></td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>client_id</td>
  <td class=xl1523697>used to create objects</td>
  <td class=xl1523697></td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>client_secret</td>
  <td class=xl1523697>used to create objects</td>
  <td class=xl1523697></td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>omfclient</td>
  <td class=xl1523697 colspan=2>client identity to be used to send OMF
  payloads. Each client identify can s<span style='display:none'>upport
  multiple secrets.</span></td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>topic</td>
  <td class=xl1523697>will be associated with omfclient</td>
  <td class=xl1523697></td>
 </tr>
 <tr height=19 style='height:14.4pt'>
  <td height=19 class=xl1523697 style='height:14.4pt'>subscription</td>
  <td class=xl1523697>will associate topic to namespace</td>
  <td class=xl1523697></td>
 </tr>
 <![if supportMisalignedColumns]>
 <tr height=0 style='display:none'>
  <td width=150 style='width:113pt'></td>
  <td width=281 style='width:211pt'></td>
  <td width=148 style='width:111pt'></td>
 </tr>
 <![endif]>
</table></p>
