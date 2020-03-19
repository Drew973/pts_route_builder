print('start')
L=QgsMapLayerRegistry.instance().mapLayersByName('cnet')[0]
f=L.fields()
newlayer=QgsVectorLayer('LineString?crs=epsg:27700','nl', 'memory')
p=newlayer.dataProvider()
p.addAttributes(f)
newlayer.commitChanges()
QgsMapLayerRegistry.instance().addMapLayer(newlayer)
print('end')

feats=L.getFeatures()
newlayer.startEditing()
for feat in feats:
    newlayer.addFeature(feat)
newlayer.commitChanges()
#refresh map?
