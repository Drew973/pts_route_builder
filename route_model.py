from qgis.PyQt import QtCore,QtGui

#from PyQt4.QtGui


#QtCore.QAbstractTableModel

#QStandardItemModel


class route_model(QtGui.QStandardItemModel):
    def __init__(self):
        super(route_model, self).__init__()
        #self.sections=[]
        


    def dropMimeData(self, data, action, row, col, parent):
       #Always move the entire row, and don't allow column "shifting"
       return super(route_model,self).dropMimeData(data, action, row, 0, parent)

        
        
  

      
        
 #   def rowCount(self, parent=QtCore.QModelIndex()):
  #      return len(self.sections) 


#    def columnCount(self, parent=QtCore.QModelIndex()):
  #      return 8       
    
    
    #def data(self, index,role=QtCore.Qt.DisplayRole):
   #     return self.sections[index.row()][index.column()]
    
    
   # def insert_section()
