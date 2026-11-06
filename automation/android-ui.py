from lxml import etree
import sys
r=etree.parse(sys.argv[1] if len(sys.argv)>1 else 'data/pdd-phone-ui.xml')
for x in r.xpath('//node[@text!="" or @content-desc!="" or @clickable="true"]'):
 print({k:x.get(k) for k in ['text','content-desc','resource-id','class','bounds','clickable']})
