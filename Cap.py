# Bouchons pour tubes
# Vincent Ballu
# Version 0.2
#
# 
# A faire: mode hexagone pour les tubes rectangulaires
# Quelques bugs avec certaines épaisseurs pour du tube carré...


from __future__ import division
import FreeCAD
import Part, math
from VectorMathLibrary import *
Vec = FreeCAD.Base.Vector


class Cap:
    def __init__(self, obj, linkface,ep=1):

        obj.addProperty("App::PropertyLinkSub","Target","Base","Target face").Target = linkface
        obj.addProperty("App::PropertyBool","Full","Parameters","Full or welding mode").Full = False
        obj.addProperty("App::PropertyFloat","Thickness","Parameters","Thickness of sheet metal").Thickness = ep
        self.find_thickness(obj)
        
        obj.Proxy = self

    def onChanged(self, obj, prop):
        pass
        
    def execute(self, obj):
        face = obj.Target[0].getSubObject(obj.Target[1][0])
        norm = face.normalAt(0,0)
        pl = obj.Placement
        dz = Vec(0,0,1)
       
        ListVertexes = face.Vertexes
        ListEdges = face.Edges
        capface = False
        print (len(ListEdges))
        # tri...
        LongSegm = [] 
        j = 0        
        for i in ListEdges:
            Ls = round(ListEdges[j].Length,3)
            if isinstance(ListEdges[j].Curve,Part.Line) and Ls not in LongSegm:  LongSegm.append(Ls)
            j +=1    
        LongSegm.sort()
        # on obtient les segments triés du + petit au + grand
        
        print ("Longueurs des segments",LongSegm) 
           
        
        if len(ListEdges) == 2:     # Cas d'un tube rond:
        
            radius0 =   ListEdges[0].Curve.Radius
            radius1 =   ListEdges[1].Curve.Radius
             
            if obj.Full:  capradius = max(radius0,radius1)
            else:         capradius = (radius0 + radius1)/2
            
            capshape = Part.makeCylinder(capradius,obj.Thickness,Vec(0,0,0),dz)
        
        if len(ListEdges) == 8 :    # Cas d'un tube rectangulaire sans arrondis
             
            if obj.Full:
                x = LongSegm[3]/2
                y = LongSegm[1]/2
            else: 
                x = LongSegm[3]/2-obj.Thickness/2
                y = LongSegm[1]/2-obj.Thickness/2
            
            p1 = Vec(x,y,0)
            p2 = Vec(x,-y,0)
            p3 = Vec(-x,-y,0)
            p4 = Vec(-x,y,0)
            L1 = Part.makeLine(p1, p2)
            L2 = Part.makeLine(p2, p3)
            L3 = Part.makeLine(p3, p4)
            L4 = Part.makeLine(p4, p1)
            wire = Part.Wire([L1,L2,L3,L4])
            capface = Part.Face(wire) 
            capshape = capface.extrude(Vec(0,0,obj.Thickness))
  
        if len(ListEdges) == 16 :   # Cas d'un tube rectangulaire avec arrondis:    
            ListRayons = [ListEdges[i].Curve.Radius for i in range(len(ListEdges)) if isinstance (ListEdges[i].Curve,Part.Circle)]
            Ray = max(ListRayons)
            ray = min(ListRayons)
            
            if obj.Full and len(LongSegm) == 4:
                r = Ray
                x1 = LongSegm[3]/2
                y1 = LongSegm[1]/2+r
                x2 = LongSegm[3]/2+r
                y2 = LongSegm[1]/2
  
            if obj.Full and len(LongSegm) == 2:
                r = Ray
                x1 = LongSegm[1]/2
                y1 = LongSegm[1]/2+Ray
                x2 = LongSegm[1]/2+Ray
                y2 = LongSegm[1]/2
            
            if obj.Full == False and len(LongSegm) == 4:
                r = (Ray+ray)/2
                x1 = (LongSegm[3]/2+LongSegm[2]/2)/2
                y1 = (LongSegm[1]/2+LongSegm[0]/2)/2+r
                x2 = (LongSegm[3]/2+LongSegm[2]/2)/2+r
                y2 = (LongSegm[1]/2+LongSegm[0]/2)/2
                
            if obj.Full == False and len(LongSegm) == 2:
                r = (Ray+ray)/2
                x1 = (LongSegm[1]/2+LongSegm[0]/2)/2
                y1 = (LongSegm[1]/2+LongSegm[0]/2)/2+r
                x2 = (LongSegm[1]/2+LongSegm[0]/2)/2+r
                y2 = (LongSegm[1]/2+LongSegm[0]/2)/2
                

            p1 = Vec(x1,y1,0)   
            p2 = Vec(x2,y2,0)
            p3 = Vec(x2,-y2,0)
            p4 = Vec(x1,-y1,0)
            p5 = Vec(-x1,-y1,0)
            p6 = Vec(-x2,-y2,0)
            p7 = Vec(-x2,y2,0)
            p8 = Vec(-x1,y1,0)
            
            c1 = Vec(x1,y2,0)
            c2 = Vec(x1,-y2,0)
            c3 = Vec(-x1,-y2,0)
            c4 = Vec(-x1,y2,0)
             
            L1 = Part.makeLine(p2,p3)
            L2 = Part.makeLine(p4,p5)
            L3 = Part.makeLine(p6,p7)  
            L4 = Part.makeLine(p8,p1)  
              
            # zero° = 3H
            # sens = anti horaire
              
            A1 = Part.makeCircle(r,c1,dz,0,90)
            A2 = Part.makeCircle(r,c2,dz,270,0)
            A3 = Part.makeCircle(r,c3,dz,180,270)
            A4 = Part.makeCircle(r,c4,dz,90,180)           
            
            wire = Part.Wire([L1,A2,L2,A3,L3,A4,L4,A1])  
            capface = Part.Face(wire)
            capshape = capface.extrude(Vec(0,0,obj.Thickness))
 
    
        
        obj.Shape = capshape
        obj.Placement = pl     
        obj.positionBySupport()    
      
        if capface:
            # Correction de 90° en cas d'inversion du tube rectangulaire
            ListLongs = [i.Length for i in ListEdges]
            ind = ListLongs.index(max(ListLongs))
            VectOrient1 = ListEdges[ind].tangentAt(0.0)
            ListEdgesCap = capface.Edges
            ListLongsCap = [i.Length for i in ListEdgesCap]
            ind = ListLongsCap.index(max(ListLongsCap))
            VectOrient2 = ListEdges[ind].tangentAt(0.0)
            AngleRelat= round(angle(VectOrient1,VectOrient2)*57.29578)+90

            obj.AttachmentOffset = FreeCAD.Placement(Vec(0,0,0),FreeCAD.Rotation(Vec(0,0,1),AngleRelat))




      
    def find_thickness(self, obj):               
        # Determination de l'épaisseur de départ:
        # On prend la même épaisseur que le tube pour être cohérent
        face = obj.Target[0].getSubObject(obj.Target[1][0])
        ListEdges = face.Edges
        print (len(ListEdges))
        # tri...
        LongSegm = [] 
        Rayons = []
        j = 0        
        for i in ListEdges:
            if isinstance(ListEdges[j].Curve,Part.Line):
                Ls = round(ListEdges[j].Length,3) 
                if Ls not in LongSegm:  LongSegm.append(Ls)
            if isinstance(ListEdges[j].Curve,Part.Circle):
                Lc = round(ListEdges[j].Curve.Radius,3)
                if Lc not in Rayons:  Rayons.append(Lc)    
            j +=1    
        LongSegm.sort()
        # print (LongSegm)
        # if len(LongSegm) == 2:
            # Lg = LongSegm[1]
            # LongSegm[1] = LongSegm[0]
            # LongSegm.append(Lg)
            # LongSegm.append(Lg)
        print (LongSegm)
        Rayons.sort()
        
        if len(ListEdges) == 2:  ep = 2*(max(Rayons)-min(Rayons))
       
        if len(ListEdges) == 8:  ep = (LongSegm[1]-LongSegm[0])/2
     
        if len(ListEdges) == 16 and len(LongSegm) == 4 :
            ep = (LongSegm[3]/2+max(Rayons))-(LongSegm[2]/2+min(Rayons))
        
        if len(ListEdges) == 16 and len(LongSegm) == 2 :
            ep = (LongSegm[1]/2+max(Rayons))-(LongSegm[0]/2+min(Rayons))

        obj.Thickness = ep            
                    
                    
 
 
def MakeCap():
   
    try:                                                        
        What = Gui.Selection.getSelectionEx()[0] 
        objet = What.Object
        subname = What.SubElementNames[0]  
        subobject = objet.getSubObject(What.SubElementNames[0])
        Nbedges = len(subobject.Edges)
       
        if isinstance(subobject,Part.Face) and (Nbedges == 2 or Nbedges == 8 or Nbedges == 16): 
            LinkFace = (objet,subname)                    
            doc = FreeCAD.activeDocument()
            obj = doc.addObject("Part::FeaturePython","Cap")   
            obj.addExtension("Part::AttachExtensionPython")
            obj.Support = LinkFace
            obj.getEnumerationsOfProperty("MapMode")
            obj.MapMode = "FlatFace"
            obj.MapPathParameter = 0
            obj.MapReversed = False   
            obj.ViewObject.Proxy = 0       
            Cap(obj,LinkFace)
        else:
            print("Selection error: Select a pipe or hollow rectangular/square.")
    except: print("Selection error: Select something first.")
   
MakeCap()