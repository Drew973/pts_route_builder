from PyQt4.QtCore import QVariant
from qgis.core import QgsField,QgsFeature

def fix_fields(layer,feat):
    ff=feat.fields()
    layer_fields=layer.fields()
    L=[]
    for field in ff:
        if not field in layer_fields:
            name=field.name()
            typ=field.typeName()
            if typ=='Real':
                L.append(QgsField(name,QVariant.Double))
            if typ=='String':
               L.append(QgsField(name,QVariant.String))
            if typ=='Integer64':
                L.append(QgsField(name,QVariant.Int))
    layer.dataProvider().addAttributes(L)
    layer.commitChanges()
    layer.updateFields()



def remake_feat(layer,feat,direction,route,desc):
    f=QgsFeature(layer.fields())#includes direction,route,desc

    for field in feat.fields():
        f.setAttribute(field.name(),feat[field.name()])
        
    f.setAttribute('direction',direction)
    f.setAttribute('route',route)
    f.setAttribute('description',desc)
    
    f.setGeometry(feat.geometry())
    return f
