#
#
# A python macro for Freecad
# to easely and quickly build profiles
# wrote by Vincent Ballu
# any remarks: vincent.ballu@gmx.com
# release as a freeware: on your risks.
# check all dimensions for a professional use!
# suitable use:
# automatic:    select an edge on 3D display (sketch, line...) then launch the macro
#               choose the profile requested, adjust options and click OK
#               ->length and placement follow the edge
# manual:       Run the macro, adjust the options and click OK
#               ->Attachment and placement can be change as a Part object
#               ->length can be change that and still manual. (Profile Length parameter)
#               ->length = 0 provide a shape to sweep or extrude
# versions:
# 10/01/2021 :  First release
# 17/01/2021 :  Pipe and round bar added
# 23/01/2021 :  Parameters for structure container changed
#               Box layout changed
#               Size give to the name profile enable
# 23/01/2021 :  Reduce code
#               Negative bevels are enable
# 27/01/2021 :  Bevels for centered profiles enable
# 31/01/2021 :  Bevel rotate option almost perfect :-)
# 07/02/2021 :  Inverted angle bevel
# 08/02/2021 :  Separate Rotate bevels
# 11/02/2021 :  Make profiles on the fly (no close the box)     
# To do:        T profiles
#               Aluminium profiles
#               and More profiles!
#               icons            
#               Limit angle bevel
#               limit attachement to edges

from PySide import QtCore, QtGui

import FreeCAD
import FreeCADGui
import math
v = FreeCAD.Base.Vector
 
g_desktop_width	 = QtGui.QDesktopWidget().screenGeometry().width()
g_desktop_height = QtGui.QDesktopWidget().screenGeometry().height()
g_win_width		 = 270
g_win_height	 = 400
g_scroll_height	 = int(g_win_height		* 0.58)
g_button_height	 = int(g_win_height		* (1.0 - 0.6) / 3.0)
g_icon_size		 = int(g_button_height	* 0.35)
g_xLoc			 = 250
g_yLoc			 = 250

global path, file_len, ind_def

class Box(QtGui.QDialog):
    def __init__(self):
   
        
        super(Box,self).__init__()
        self.initUI(0,ind_def)
          
    def initUI(self,fam_init,size_init):
    
        self.fams = recherche_fams()
        self.fam  = self.fams[fam_init]
        self.dims = recherche_dims(self.fam)
        self.dim = self.dims[size_init]
        
        self.MakeFillet = True
        self.Reverse = False
        self.HeightCentered = False
        self.WidthCentered = False
        self.SizeName = False
              
        self.update_data()
                   
        self.P_length = 100
        
        
        self.setGeometry(g_xLoc,g_yLoc,g_win_width,g_win_height)
        self.setWindowTitle("Profile Warehouse")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # lay = QtGui.QGridLayout(self)
        
        #Labels
        self.label_title1 = QtGui.QLabel("Family", self)
        newFont=QtGui.QFont(self.label_title1.font())
        newFont.setPointSize(10)
        self.label_title1.setFont(newFont)
        self.label_title1.move(50, 8)
        
        self.label_title2 = QtGui.QLabel("Size", self)
        newFont=QtGui.QFont(self.label_title2.font())
        newFont.setPointSize(10)
        self.label_title2.setFont(newFont)
        self.label_title2.move(190, 8)
        
        self.label_height = QtGui.QLabel("Height or diameter", self)
        self.label_height.move (10, 65)
        self.label_width = QtGui.QLabel("Width", self)
        self.label_width.move (10, 90)
        self.label_mainthickness = QtGui.QLabel("Main Thickness", self)
        self.label_mainthickness.move (10, 115)
        self.label_flangethickness = QtGui.QLabel("Flange Thickness", self)
        self.label_flangethickness.move (10, 140)
        
        self.label_length = QtGui.QLabel("Length", self)
        self.label_length.move (10, 165)
        self.label_length = QtGui.QLabel("Large radius", self)
        self.label_length.move (10, 190)
        self.label_length = QtGui.QLabel("Small radius", self)
        self.label_length.move (10, 215)
        
        self.label_attach= QtGui.QLabel("",self)
        newFont=QtGui.QFont(self.label_attach.font())
        newFont.setPointSize(10)
        self.label_attach.setFont(newFont)
        self.label_attach.move (10, 250)
        
        self.update_selection("","")
    
        # checkboxes
        self.checkbox1 = QtGui.QCheckBox("Make Fillets", self)
        self.checkbox1.toggle()
        self.checkbox1.clicked.connect(self.onCheckbox1)
        self.checkbox1.move(10,275)
        self.checkbox2 = QtGui.QCheckBox("Reverse Attachment", self)
        self.checkbox2.clicked.connect(self.onCheckbox2)
        self.checkbox2.move(140,275)
        self.checkbox3 = QtGui.QCheckBox("Height Centered", self)
        self.checkbox3.clicked.connect(self.onCheckbox3)
        self.checkbox3.move(10,300)
        self.checkbox4 = QtGui.QCheckBox("Width Centered", self)
        self.checkbox4.clicked.connect(self.onCheckbox4)
        self.checkbox4.move(140,300)
        self.checkbox5 = QtGui.QCheckBox("Include size in object name", self)
        self.checkbox5.clicked.connect(self.onCheckbox5)
        self.checkbox5.move(10,325)

        # Combo boxes
        # familly
        self.ComboStyle = QtGui.QComboBox(self)
        self.ComboStyle.setToolTip("Choose kind of profile")
        self.ComboStyle.addItems(self.fams)
        self.ComboStyle.setCurrentIndex(self.fams.index(self.fam))
        self.ComboStyle.activated[str].connect(self.onComboStyle_Changed)
        self.ComboStyle.move (10,30)
        # Size
        self.ComboSize = QtGui.QComboBox(self)
        self.ComboSize.setToolTip("Choose size")
        self.ComboSize.addItems(self.dims)
        self.ComboSize.setCurrentIndex(self.dims.index(self.dim))
        self.ComboSize.activated[str].connect(self.onComboSize_Changed)
        self.ComboSize.move (160,30)

        # Spin Boxes
        self.SB_height = QtGui.QDoubleSpinBox(self)
        self.SB_height.setToolTip ("Adjust height")
        self.SB_height.setPrefix("")
        self.SB_height.setSuffix("")
        self.SB_height.setDecimals(1)
        self.SB_height.setMinimum(0.1)
        self.SB_height.setMaximum(1000.0)
        self.SB_height.setSingleStep(0.1)
        self.SB_height.setProperty("value",self.P_height)
        self.SB_height.setObjectName("height")
        self.SB_height.move(160,60)

        self.SB_width = QtGui.QDoubleSpinBox(self)
        self.SB_width.setToolTip ("Adjust width")
        self.SB_width.setPrefix("")
        self.SB_width.setSuffix("")
        self.SB_width.setDecimals(1)
        self.SB_width.setMinimum(0.0)
        self.SB_width.setMaximum(1000.0)
        self.SB_width.setSingleStep(0.1)
        self.SB_width.setProperty("value",self.P_width)
        self.SB_width.setObjectName("width")
        self.SB_width.move(160,85)

        self.SB_mainthickness = QtGui.QDoubleSpinBox(self)
        self.SB_mainthickness.setToolTip ("Adjust main or web thickness")
        self.SB_mainthickness.setPrefix("")
        self.SB_mainthickness.setSuffix("")
        self.SB_mainthickness.setDecimals(2)
        self.SB_mainthickness.setMinimum(0)
        self.SB_mainthickness.setMaximum(100.0)
        self.SB_mainthickness.setSingleStep(0.01)
        self.SB_mainthickness.setProperty("value",self.P_mainthickness)
        self.SB_mainthickness.setObjectName("mainthickness")
        self.SB_mainthickness.move(160,110)
        
        self.SB_flangethickness = QtGui.QDoubleSpinBox(self)
        self.SB_flangethickness.setToolTip ("Adjust flange thickness")
        self.SB_flangethickness.setPrefix("")
        self.SB_flangethickness.setSuffix("")
        self.SB_flangethickness.setDecimals(1)
        self.SB_flangethickness.setMinimum(0)
        self.SB_flangethickness.setMaximum(100.0)
        self.SB_flangethickness.setSingleStep(0.1)
        self.SB_flangethickness.setProperty("value",self.P_flangethickness)
        self.SB_flangethickness.setObjectName("flangethickness")
        self.SB_flangethickness.move(160,135)

        self.SB_length = QtGui.QDoubleSpinBox(self)
        self.SB_length.setToolTip ("Set length if not attached")
        self.SB_length.setPrefix("")
        self.SB_length.setSuffix("")
        self.SB_length.setDecimals(1)
        self.SB_length.setMinimum(0)
        self.SB_length.setMaximum(24000.0)
        self.SB_length.setSingleStep(0.1)
        self.SB_length.setProperty("value",self.P_length)
        self.SB_length.setObjectName("length")
        self.SB_length.move(160,160)
        
        self.SB_Radius1 = QtGui.QDoubleSpinBox(self)
        self.SB_Radius1.setToolTip ("Adjust Radius 1")
        self.SB_Radius1.setPrefix("")
        self.SB_Radius1.setSuffix("")
        self.SB_Radius1.setDecimals(1)
        self.SB_Radius1.setMinimum(0)
        self.SB_Radius1.setMaximum(50)
        self.SB_Radius1.setSingleStep(0.1)
        self.SB_Radius1.setProperty("value",self.P_radius1)
        self.SB_Radius1.setObjectName("radius1")
        self.SB_Radius1.move(160,185)
        
        self.SB_Radius2 = QtGui.QDoubleSpinBox(self)
        self.SB_Radius2.setToolTip ("Adjust Radius 2")
        self.SB_Radius2.setPrefix("")
        self.SB_Radius2.setSuffix("")
        self.SB_Radius2.setDecimals(1)
        self.SB_Radius2.setMinimum(0)
        self.SB_Radius2.setMaximum(50)
        self.SB_Radius2.setSingleStep(0.1)
        self.SB_Radius2.setProperty("value",self.P_radius2)
        self.SB_Radius2.setObjectName("radius2")
        self.SB_Radius2.move(160,210)

        # cancel button
        cancelButton = QtGui.QPushButton('Close', self)
        cancelButton.clicked.connect(self.onCancel)
        cancelButton.setAutoDefault(True)
        cancelButton.move(50, 350)
        # OK button
        okButton = QtGui.QPushButton('Create', self)
        okButton.clicked.connect(self.onOk)
        okButton.move(150, 350)
 
        
        self.show()
        
    def onCancel(self):
       
        self.close()

    def onOk(self):
    
        if self.SizeName: name = self.fam + "_" + self.dim + "_"
        else: name = self.fam
            
        obj=doc.addObject("Part::FeaturePython",name) 
        obj.addExtension("Part::AttachExtensionPython","obj")
        obj.ViewObject.Proxy=0
        viewObject = Gui.ActiveDocument.getObject(obj.Name)
        viewObject.DisplayMode = "Flat Lines"
        linksub = ""
        
        try:
            selobj = Gui.Selection.getSelectionEx()[0]
            linksub = (selobj.Object, (selobj.SubElementNames[0]))
            selsubobj = selobj.SubObjects[0]
            feature = selobj.Object
            edgeName = selobj.SubElementNames[0]
            l = selsubobj.Length
            obj.MapMode = "NormalToEdge"
            obj.Support =  (feature, edgeName)
            if self.Reverse == False:
                obj.MapPathParameter = 1
            else:
                obj.MapPathParameter = 0
                obj.MapReversed = True
       
        except: print ("no edge selected")
        
        w = self.SB_width.value()
        h = self.SB_height.value()
        ft = self.SB_flangethickness.value()
        mt = self.SB_mainthickness.value()
        r1 = self.SB_Radius1.value()
        r2 = self.SB_Radius2.value()
        if linksub=="":  l = self.SB_length.value()
      
        p = float(self.Weight)
        
        if self.fam == "Flat Sections" or  self.fam == "Square" :  
            self.Makefillet = False
            print(self.Makefillet)
               
        Profile(obj,linksub,w,h,mt,ft,r1,r2,l,p,self.MakeFillet,self.HeightCentered,self.WidthCentered,self.fam)  
        d = FreeCAD.activeDocument()
        d.recompute()
        print("new profile")
       

    def onCheckbox1(self):
        if self.MakeFillet == False:
            self.MakeFillet = True
        else:
            self.MakeFillet = False

    def onCheckbox2(self):
        if self.Reverse == False:
            self.Reverse = True
        else:
            self.Reverse = False

    def onCheckbox3(self):
        if self.HeightCentered == False:
            self.HeightCentered = True
        else:
            self.HeightCentered = False   

    def onCheckbox4(self):
        if self.WidthCentered == False:
            self.WidthCentered = True
        else:
            self.WidthCentered = False
            
    def onCheckbox5(self):
        if self.SizeName == False:
            self.SizeName = True
        else:
            self.SizeName = False
       
    def onComboStyle_Changed(self,texte):
        self.fam = texte
        self.dims = recherche_dims(self.fam)
        
        self.dim = self.dims[ind_def]
        self.ComboSize.clear()
        self.ComboSize.addItems(self.dims)
        self.ComboSize.setCurrentIndex(self.dims.index(self.dim))
        self.update_data()
        self.update_box()

    def onComboSize_Changed(self,texte):
        self.dim = texte
        self.update_data()
        self.update_box()
        
    def update_data(self):
        self.data = extrait_data(self.fam,self.dim)
        try:   self.P_height          = self.data[recherche_ind(self.fam,"Height")]
        except:self.P_height          = 0
        try:   self.P_width           = self.data[recherche_ind(self.fam,"Width")]
        except:self.P_width           = 0
        try:   self.P_mainthickness   = self.data[recherche_ind(self.fam,"Thickness")]
        except:self.P_mainthickness   = 0
        try:   self.P_flangethickness = self.data[recherche_ind(self.fam,"Flange Thickness")]
        except:self.P_flangethickness = 0
        try:   self.P_radius1         = self.data[recherche_ind(self.fam,"Radius1")]
        except:self.P_radius1         = 0
        try:   self.P_radius2         = self.data[recherche_ind(self.fam,"Radius2")]
        except:self.P_radius2         = 0
        try:   self.Weight            = self.data[recherche_ind(self.fam,"Weight")] 
        except:self.Weight            = 0
    
    def update_box(self):
        self.SB_height.setProperty          ("value",self.P_height)
        self.SB_width.setProperty           ("value",self.P_width)
        self.SB_mainthickness.setProperty   ("value",self.P_mainthickness)
        self.SB_flangethickness.setProperty ("value",self.P_flangethickness)
        self.SB_length.setProperty          ("value",self.P_length)
        self.SB_Radius1.setProperty         ("value",self.P_radius1)
        self.SB_Radius2.setProperty         ("value",self.P_radius2)
        
    def update_selection(self,new_obj,new_sub):
        
        try:                                            # first run
            selobj = Gui.Selection.getSelectionEx()[0]
            edgeName = selobj.SubElementNames[0]
            sel = FreeCADGui.Selection.getSelectionEx()	
            objname = sel[0].ObjectName
            nom = "Attachment: "+ objname + " / " + edgeName	
        except:
            nom = "Attachment: None                                          "
            
        if new_obj and new_sub: nom = "Attachment: " + new_obj + " / " + new_sub    
 
        self.label_attach.setText(nom)
        # print("updated attachement :",nom)


class Profile:
   def __init__(self,obj,linksub,init_w,init_h,init_mt,init_ft,init_r1,init_r2,init_lenobj,init_wg,init_mf,init_hc,init_wc,type):
  
      obj.addProperty("App::PropertyFloat","ProfileHeight","Profile","",).ProfileHeight = init_h
      obj.addProperty("App::PropertyFloat","ProfileWidth","Profile","").ProfileWidth = init_w
      obj.addProperty("App::PropertyFloat","ProfileLength","Profile","").ProfileLength = init_lenobj
      
      obj.addProperty("App::PropertyFloat","MainThickness","Profile","Thickness of all the profile or the web").MainThickness = init_mt
      obj.addProperty("App::PropertyFloat","FlangeThickness","Profile","Thickness of the flanges").FlangeThickness = init_ft
      
      obj.addProperty("App::PropertyFloat","LargeRadius","Profile","Large radius").LargeRadius = init_r1
      obj.addProperty("App::PropertyFloat","SmallRadius","Profile","Small radius").SmallRadius = init_r2
      obj.addProperty("App::PropertyBool","MakeFillet","Profile","Wheter to draw the fillets or not").MakeFillet = init_mf
      
      obj.addProperty("App::PropertyFloat","BevelStartCut1","Profile","Bevel on First axle at the start of the profile").BevelStartCut1 = 0
      obj.addProperty("App::PropertyFloat","BevelEndCut1","Profile","Bevel on First axle at the end of the profile").BevelEndCut1 = 0
      obj.addProperty("App::PropertyFloat","BevelStartCut2","Profile","Rotate the cut on Second axle at the start of the profile").BevelStartCut2 = 0
      obj.addProperty("App::PropertyFloat","BevelEndCut2","Profile","Rotate the cut on Second axle at the end of the profile").BevelEndCut2 = 0
       
      obj.addProperty("App::PropertyFloat","ApproxWeight","Base","Approximate weight in Kilogramme").ApproxWeight= init_wg*init_lenobj/1000

      obj.addProperty("App::PropertyBool","HeightCentered","Profile","Choose corner or profile centre as origin").HeightCentered = init_hc
      obj.addProperty("App::PropertyBool","WidthCentered","Profile","Choose corner or profile centre as origin").WidthCentered = init_wc
      
      if type == "UPE":
        obj.addProperty("App::PropertyBool","UPN","Profile","UPE style or UPN style").UPN = False
        obj.addProperty("App::PropertyFloat","FlangeAngle","Profile").FlangeAngle = 4.57
      if type == "UPN":
        obj.addProperty("App::PropertyBool","UPN","Profile","UPE style or UPN style").UPN = True
        obj.addProperty("App::PropertyFloat","FlangeAngle","Profile").FlangeAngle = 4.57     
       
      if type == "IPE" or type == "HEA" or type == "HEB" or type == "HEM":
        obj.addProperty("App::PropertyBool","IPN","Profile","IPE/HEA style or IPN style").IPN = False
        obj.addProperty("App::PropertyFloat","FlangeAngle","Profile").FlangeAngle = 8
      if type == "IPN":
        obj.addProperty("App::PropertyBool","IPN","Profile","IPE/HEA style or IPN style").IPN = True
        obj.addProperty("App::PropertyFloat","FlangeAngle","Profile").FlangeAngle = 8
       
      obj.addProperty("App::PropertyLength","Width","Structure","Parameter for structure").Width = obj.ProfileWidth     # Propertylength for structure
      obj.addProperty("App::PropertyLength","Height","Structure","Parameter for structure").Height = obj.ProfileLength  # Propertylength for structure
      obj.addProperty("App::PropertyLength","Length","Structure","Parameter for structure",).Length = obj.ProfileHeight # Propertylength for structure
      obj.setEditorMode("Width", 1)         # user doesn't change !
      obj.setEditorMode("Height", 1)
      obj.setEditorMode("Length", 1)

      if linksub: obj.addProperty("App::PropertyLinkSub","Target","Base","Target face").Target = linksub
      
      self.WM = init_wg
      self.type = type
      obj.Proxy = self
 
   def onChanged(self, obj, p):
      if p == "ProfileWidth" or p == "ProfileHeight" or p == "Thickness" \
         or p == "FilletRadius"  or p == "Centered" or p == "Length"\
         or p == "BevelStartCut1" or p == "BevelEndCut1" \
         or p == "BevelStartCut2" or p == "BevelEndCut2" :
        
        self.execute(obj)

   def execute(self, obj):
           
        try:
            L = obj.Target[0].getSubObject(obj.Target[1][0]).Length
            obj.ProfileLength = L
        except:   
            L = obj.ProfileLength 
          
        obj.ApproxWeight = self.WM*L/1000
        W = obj.ProfileWidth
        H = obj.ProfileHeight
        obj.Height = L
        pl = obj.Placement
        TW = obj.MainThickness
        TF = obj.FlangeThickness
  
        w = 0
        h = 0
        R = obj.LargeRadius
        r = obj.SmallRadius
        d = v(0,0,1)
        B1Y = obj.BevelStartCut1
        B2Y = obj.BevelEndCut1
        B1X = -obj.BevelStartCut2
        B2X = obj.BevelEndCut2
 
        if W == 0 : W = H
        k =  10 * max (H/W,W/H) 
       
        if obj.WidthCentered == True:  w = -W/2
        if obj.HeightCentered == True: h = -H/2   
        
        if self.type == "Equal Leg Angles" or self.type == "Unequal Leg Angles":      
            if obj.MakeFillet == False:
                p1 = v(0+w,0+h,0)
                p2 = v(0+w,H+h,0)
                p3 = v(TW+w,H+h,0)
                p4 = v(TW+w,TW+h,0)
                p5 = v(W+w,TW+h,0)
                p6 = v(W+w,0+h,0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p1)
                    
                wire1 = Part.Wire([L1,L2,L3,L4,L5,L6])
                
            if obj.MakeFillet == True:
                p1 = v(0+w,0+h,0)
                p2 = v(0+w,H+h,0)
                p3 = v(TW-r+w,H+h,0)
                p4 = v(TW+w,H-r+h,0)
                p5 = v(TW+w,TW+R+h,0)
                p6 = v(TW+R+w,TW+h,0)
                p7 = v(W-r+w,TW+h,0)
                p8 = v(W+w,TW-r+h,0)
                p9 = v(W+w,0+h,0)
                c1 = v(TW-r+w,H-r+h,0)
                c2 = v(TW+R+w,TW+R+h,0)
                c3 = v(W-r+w,TW-r+h,0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p4, p5)
                L4 = Part.makeLine(p6, p7)
                L5 = Part.makeLine(p8, p9)
                L6 = Part.makeLine(p9, p1)
                A1 = Part.makeCircle(r,c1,d,0,90)
                A2 = Part.makeCircle(R,c2,d,180,270)
                A3 = Part.makeCircle(r,c3,d,0,90)
                   
                wire1 = Part.Wire([L1,L2,A1,L3,A2,L4,A3,L5,L6])
                
            p = Part.Face(wire1)        
        
        if self.type == "Flat Sections" or  self.type == "Square"  or  self.type == "Square Hollow" or  self.type == "Rectangular Hollow":
            wire1=wire2=0
            
            if self.type == "Square" or self.type == "Flat Sections":
                p1 = v(0+w,0+h,0)
                p2 = v(0+w,H+h,0)
                p3 = v(W+w,H+h,0)
                p4 = v(W+w,0+h,0)
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                wire1 = Part.Wire([L1,L2,L3,L4])
                
            if obj.MakeFillet == False and (self.type == "Square Hollow" or self.type == "Rectangular Hollow") :
                p1 = v(0+w,0+h,0)
                p2 = v(0+w,H+h,0)
                p3 = v(W+w,H+h,0)
                p4 = v(W+w,0+h,0)
                p5 = v(TW+w,TW+h,0)
                p6 = v(TW+w,H+h-TW,0)
                p7 = v(W+w-TW,H+h-TW,0)
                p8 = v(W+w-TW,TW+h,0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p5)
                    
                wire1 = Part.Wire([L1,L2,L3,L4])
                wire2 = Part.Wire([L5,L6,L7,L8])
            
            if obj.MakeFillet == True and (self.type == "Square Hollow" or self.type == "Rectangular Hollow") :
                p1 = v(0+w,  0+R+h, 0)
                p2 = v(0+w,  H-R+h, 0)
                p3 = v(R+w,  H+h,   0)
                p4 = v(W-R+w,H+h,   0)
                p5 = v(W+w,  H-R+h, 0)
                p6 = v(W+w,  R+h,   0)
                p7 = v(W-R+w,0+h,   0)
                p8 = v(R+w,  0+h,   0)
                
                c1 = v(R+w,  R+h,   0)
                c2 = v(R+w,  H-R+h, 0)
                c3 = v(W-R+w,H-R+h, 0)
                c4 = v(W-R+w,R+h,   0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(R,c1,d,180,270)
                A2 = Part.makeCircle(R,c2,d,90,180)
                A3 = Part.makeCircle(R,c3,d,0,90)
                A4 = Part.makeCircle(R,c4,d,270,0)
                  
                wire1 = Part.Wire([L1,A2,L2,A3,L3,A4,L4,A1])
            
                p1 = v(TW+w,    TW+r+h,    0)
                p2 = v(TW+w,    H-TW-r+h,  0)
                p3 = v(TW+r+w,  H-TW+h,    0)
                p4 = v(W-TW-r+w,H-TW+h,    0)
                p5 = v(W-TW+w,  H-TW-r+h,  0)
                p6 = v(W-TW+w,  TW+r+h,    0)
                p7 = v(W-TW-r+w,TW+h,      0)
                p8 = v(TW+r+w,  TW+h,      0)
                
                c1 = v(TW+r+w,  TW+r+h,    0)
                c2 = v(TW+r+w,  H-TW-r+h,  0)
                c3 = v(W-TW-r+w,H-TW-r+h,  0)
                c4 = v(W-TW-r+w,TW+r+h,    0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(r,c1,d,180,270)
                A2 = Part.makeCircle(r,c2,d,90,180)
                A3 = Part.makeCircle(r,c3,d,0,90)
                A4 = Part.makeCircle(r,c4,d,270,0)
           
                wire2 = Part.Wire([L1,A2,L2,A3,L3,A4,L4,A1])  
                
            if wire2:
                p1 = Part.Face(wire1)
                p2 = Part.Face(wire2)  
                p = p1.cut(p2)
            else:
                p = Part.Face(wire1)    
 
        if self.type == "UPE" or self.type == "UPN":
            if obj.MakeFillet == False:                          # UPE ou UPN sans arrondis
           
                Yd = 0
                if obj.UPN == True: Yd = (W/4)*math.tan(math.pi*obj.FlangeAngle/180)  
                
                p1 = v(w,           h,0)
                p2 = v(w,           H+h,0)
                p3 = v(w+W,         H+h,0)
                p4 = v(W+w,         h,0)
                p5 = v(W+w+Yd-TW,   h,0)
                p6 = v(W+w-Yd-TW,   H+h-TF,0)
                p7 = v(w+TW+Yd,     H+h-TF,0)
                p8 = v(w+TW-Yd,     h,0)
         
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p1)
             
                wire1 = Part.Wire([L1,L2,L3,L4,L5,L6,L7,L8])
                
            if obj.MakeFillet == True and obj.UPN == False:      # UPE avec arrondis
                    
                p1 =  v(w,          h,0)
                p2 =  v(w,          H+h,0)
                p3 =  v(w+W,        H+h,0)
                p4 =  v(W+w,        h,0)
                p5 =  v(W+w-TW+r,   h,0)
                p6 =  v(W+w-TW,     h+r,0)
                p7 =  v(W+w-TW,     H+h-TF-R,0)
                p8 =  v(W+w-TW-R,   H+h-TF,0)
                p9 =  v(w+TW+R,     H+h-TF,0)
                p10 = v(w+TW,       H+h-TF-R,0)
                p11 = v(w+TW,       h+r,0)
                p12 = v(w+TW-r,     h,0)
               
                C1 = v(w+TW-r,h+r,0)
                C2 = v(w+TW+R,H+h-TF-R,0)
                C3 = v(W+w-TW-R,H+h-TF-R,0)
                C4 = v(W+w-TW+r,r+h,0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p10, p11)
                L8 = Part.makeLine(p12, p1)
                
                        
                A1 = Part.makeCircle(r,C1,d,270,0)
                A2 = Part.makeCircle(R,C2,d,90,180)
                A3 = Part.makeCircle(R,C3,d,0,90)
                A4 = Part.makeCircle(r,C4,d,180,270)
                
                   
                wire1 = Part.Wire([L1,L2,L3,L4,A4,L5,A3,L6,A2,L7,A1,L8])
            
            if obj.MakeFillet == True and obj.UPN == True:       # UPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi*angarc/180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)
                
                cot1 = r*sina
                y11 = r-cot1
                cot2 = (H/2-r)*tana
                cot3 = cot1*tana
                x11 = TW-cot2-cot3
                xc1 = TW-cot2-cot3-r*cosa
                yc1 = r
                cot8 = (H/2-R-TF+R*sina)*tana
                x10 = TW+cot8
                y10 = H-TF-R+R*sina
                xc2 = cot8+R*cosa+TW
                yc2 = H-TF-R
                x12 = TW-cot2-cot3-r*cosa
                y12 = 0
                x9 = cot8+R*cosa+TW
                y9 = H-TF
                xc3 = W-xc2
                yc3 = yc2
                xc4 = W-xc1
                yc4 = yc1
                x1 = 0 
                y1 = 0
                x2 = 0
                y2 = H
                x3 = W
                y3 = H
                x4 = W
                y4 = 0
                x5 = W-x12
                y5 = 0
                x6 = W-x11
                y6 = y11
                x7 = W-x10
                y7 = y10
                x8 = W-x9
                y8 = y9
           
                c1 = v(xc1+w,yc1+h,0)
                c2 = v(xc2+w,yc2+h,0)
                c3 = v(xc3+w,yc3+h,0)
                c4 = v(xc4+w,yc4+h,0)
                
                p1  = v(x1+w,y1+h,0)
                p2  = v(x2+w,y2+h,0)
                p3  = v(x3+w,y3+h,0)
                p4  = v(x4+w,y4+h,0)
                p5  = v(x5+w,y5+h,0)
                p6  = v(x6+w,y6+h,0)
                p7  = v(x7+w,y7+h,0)
                p8  = v(x8+w,y8+h,0)
                p9  = v(x9+w,y9+h,0)
                p10 = v(x10+w,y10+h,0)
                p11 = v(x11+w,y11+h,0)
                p12 = v(x12+w,y12+h,0)
             
                A1 = Part.makeCircle(r,c1,d,270,0-angarc)
                A2 = Part.makeCircle(R,c2,d,90,180-angarc)
                A3 = Part.makeCircle(R,c3,d,0+angarc,90)
                A4 = Part.makeCircle(r,c4,d,180+angarc,270)
                    
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p10, p11)
                L8 = Part.makeLine(p12, p1)
               
                wire1 = Part.Wire([L1,L2,L3,L4,A4,L5,A3,L6,A2,L7,A1,L8])

            p = Part.Face(wire1)    

        if self.type == "IPE" or self.type == "IPN" or self.type == "HEA" or self.type == "HEB" or self.type == "HEM":
            XA1 = W/2-TW/2                   # face gauche du web
            XA2 = W/2+TW/2                   # face droite du web
            if obj.MakeFillet == False:      # IPE ou IPN sans arrondis
                Yd = 0
                if obj.IPN == True: Yd = (W/4)*math.tan(math.pi*obj.FlangeAngle/180)  
                
                p1 =  v(0+w,0+h,0)
                p2 =  v(0+w,TF+h-Yd,0)
                p3 =  v(XA1+w,TF+h+Yd,0)
                p4 =  v(XA1+w,H-TF+h-Yd,0)
                p5 =  v(0+w,H-TF+h+Yd,0)
                p6 =  v(0+w,H+h,0)
                p7 =  v(W+w,H+h,0)
                p8 =  v(W+w,H-TF+h+Yd,0)
                p9 =  v(XA2+w,H-TF+h-Yd,0)
                p10 = v(XA2+w,TF+h+Yd,0)
                p11 = v(W+w,TF+h-Yd,0)
                p12 = v(W+w,0+h,0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p9)
                L9 = Part.makeLine(p9, p10)
                L10 = Part.makeLine(p10,p11)
                L11 = Part.makeLine(p11,p12)
                L12 = Part.makeLine(p12,p1)
                    
                wire1 = Part.Wire([L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12])
                
            if obj.MakeFillet == True and obj.IPN == False:      # IPE avec arrondis
                p1 =  v(0+w,0+h,0)
                p2 =  v(0+w,TF+h,0)
                p3 =  v(XA1-R+w,TF+h,0)
                p4 =  v(XA1+w,TF+R+h,0)
                p5 =  v(XA1+w,H-TF-R+h,0)
                p6 =  v(XA1-R+w,H-TF+h,0)
                p7 =  v(0+w,H-TF+h,0)
                p8 =  v(0+w,H+h,0)
                p9 =  v(W+w,H+h,0)
                p10 = v(W+w,H-TF+h,0)
                p11 = v(XA2+R+w,H-TF+h,0)
                p12 = v(XA2+w,H-TF-R+h,0)
                p13 = v(XA2+w,TF+R+h,0)
                p14 = v(XA2+R+w,TF+h,0)
                p15 = v(W+w,TF+h,0)
                p16 = v(W+w,0+h,0)
                
                c1 = v(XA1-R+w,TF+R+h,0)
                c2 = v(XA1-R+w,H-TF-R+h,0)
                c3 = v(XA2+R+w,H-TF-R+h,0)
                c4 = v(XA2+R+w,TF+R+h,0)
                
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p4, p5)
                L4 = Part.makeLine(p6, p7)
                L5 = Part.makeLine(p7, p8)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p9, p10)
                L8 = Part.makeLine(p10, p11)
                L9 = Part.makeLine(p12, p13)
                L10 = Part.makeLine(p14, p15)
                L11 = Part.makeLine(p15, p16)
                L12 = Part.makeLine(p16, p1)
                
                A1 = Part.makeCircle(R,c1,d,270,0)
                A2 = Part.makeCircle(R,c2,d,0,90)
                A3 = Part.makeCircle(R,c3,d,90,180)
                A4 = Part.makeCircle(R,c4,d,180,270)
                   
                wire1 = Part.Wire([L1,L2,A1,L3,A2,L4,L5,L6,L7,L8,A3,L9,A4,L10,L11,L12])
            
            if obj.MakeFillet == True and obj.IPN == True:       # IPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi*angarc/180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)
                cot1 = W/4*tana     #1,47
                cot2 = TF-cot1      #4,42
                cot3 = r*cosa       #1,98
                cot4 = r-cot3*tana  #1,72
                cot5 = cot4*tana    #0,24
                cot5 = cot2+cot5    #4,66
                cot6 = R*sina       #0,55
                cot7 = W/4-R-TW/2   #4,6
                cot8 = cot6+cot7    #5,15
                cot9 = cot7*tana    #0,72
                cot10 = R*cosa      #3,96
                
                xc1 = r
                yc1 = cot5-cot3
                c1 = v(xc1+w,yc1+h,0)
                
                xc2 = W/2-TW/2-R
                yc2 = cot9+TF+cot10
                c2 = v(xc2+w,yc2+h,0)
                
                xc3 = xc2
                yc3 = H-yc2
                c3 = v(xc3+w,yc3+h,0)
                
                xc4 = xc1
                yc4 = H-yc1
                c4 = v(xc4+w,yc4+h,0)
                   
                xc5 = W-xc1
                yc5 = yc4
                c5 = v(xc5+w,yc5+h,0)
                
                xc6 = W-xc2
                yc6 = yc3
                c6 = v(xc6+w,yc6+h,0)
                
                xc7 = xc6
                yc7 = yc2
                c7 = v(xc7+w,yc7+h,0)
                
                xc8 = xc5
                yc8 = yc1
                c8 = v(xc8+w,yc8+h,0)
                
                A1 = Part.makeCircle(r,c1,d,90+angarc,180)
                A2 = Part.makeCircle(R,c2,d,270+angarc,0)
                A3 = Part.makeCircle(R,c3,d,0,90-angarc)
                A4 = Part.makeCircle(r,c4,d,180,270-angarc)
                A5 = Part.makeCircle(r,c5,d,270+angarc,0)
                A6 = Part.makeCircle(R,c6,d,90+angarc,180)
                A7 = Part.makeCircle(R,c7,d,180,270-angarc)
                A8 = Part.makeCircle(r,c8,d,0,90-angarc)
                
                xp1 = 0
                yp1 = 0
                p1 = v(xp1+w,yp1+h,0)
                
                xp2 = 0
                yp2 = cot5-cot3
                p2  = v(xp2+w,yp2+h,0)
                
                xp3 = cot4
                yp3 = cot5
                p3 = v(xp3+w,yp3+h,0)
                
                xp4 = W/4+cot8
                yp4 = TF+cot9
                p4 = v(xp4+w,yp4+h,0)
                
                xp5 = W/2-TW/2
                yp5 = yc2
                p5 = v(xp5+w,yp5+h,0)
                
                xp6 = xp5
                yp6 = H-yp5
                p6 = v(xp6+w,yp6+h,0)
                
                xp7 = xp4
                yp7 = H-yp4
                p7 = v(xp7+w,yp7+h,0)
                
                xp8 = xp3
                yp8 = H-yp3
                p8 = v(xp8+w,yp8+h,0)
                
                xp9 = xp2
                yp9 = H - yp2
                p9 = v(xp9+w,yp9+h,0)
                
                xp10 = xp1
                yp10 = H
                p10 = v(xp10+w,yp10+h,0)
                
                xp11 = W
                yp11 = H
                p11 = v(xp11+w,yp11+h,0)
                
                xp12 = xp11
                yp12 = yp9
                p12 = v(xp12+w,yp12+h,0)
                
                xp13 = W-xp8
                yp13 = yp8
                p13 = v(xp13+w,yp13+h,0)
                
                xp14 = W-xp7
                yp14 = yp7
                p14 = v(xp14+w,yp14+h,0)
                
                xp15 = W-xp6
                yp15 = yp6
                p15 = v(xp15+w,yp15+h,0)
                
                xp16 = W-xp5
                yp16 = yp5
                p16 = v(xp16+w,yp16+h,0)
                
                xp17 = W-xp4
                yp17 = yp4
                p17 = v(xp17+w,yp17+h,0)
                
                xp18 = W-xp3
                yp18 = yp3
                p18 = v(xp18+w,yp18+h,0)
                
                xp19 = W-xp2
                yp19 = yp2
                p19 = v(xp19+w,yp19+h,0)
                
                xp20 = W
                yp20 = 0
                p20 = v(xp20+w,yp20+h,0)
                  
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                L5 = Part.makeLine(p9, p10)
                L6 = Part.makeLine(p10, p11)
                L7 = Part.makeLine(p11, p12)
                L8 = Part.makeLine(p13, p14)
                L9 = Part.makeLine(p15, p16)
                L10 = Part.makeLine(p17, p18)
                L11 = Part.makeLine(p19, p20)
                L12 = Part.makeLine(p20, p1)
                    
                wire1 = Part.Wire([L1,A1,L2,A2,L3,A3,L4,A4,L5,L6,L7,A5,L8,A6,L9,A7,L10,A8,L11,L12])
           
            p = Part.Face(wire1)    
     
        if self.type == "Round bar" or self.type == "Pipe":
            c = v(H/2+w,H/2+h,0)
            A1 = Part.makeCircle(H/2,c,d,0,360)   
            A2 = Part.makeCircle((H-TW)/2,c,d,0,360)       
            wire1 = Part.Wire([A1])
            wire2 = Part.Wire([A2])
            if TW:
                p1 = Part.Face(wire1)
                p2 = Part.Face(wire2)  
                p = p1.cut(p2)
            else:
                p = Part.Face(wire1)
      
        if L:                                   
            ProfileFull = p.extrude(v(0,0,L))
            ProfileTemp = ProfileFull
 
                      
            Z1Y = W*math.tan(math.pi*B1Y/180)
            Z2Y = W*math.tan(math.pi*B2Y/180)
            Z1X = W*math.tan(math.pi*-B1X/180)
            Z2X = W*math.tan(math.pi*B2X/180)
            ZC1 = H*k
            ZC2 = H*k
             
            if B2Y: 
                if obj.WidthCentered == False: 
                    p1 = v(w,h,     L)
                    p2 = v(W+w,h,   L+Z2Y)
                    p3 = v(W+w,h,   L+ZC2)
                    p4 = v(w,h,     L+ZC2)
                    ProfileExt = ProfileTemp.fuse(p.extrude(v(0,0,L+ZC2)))
                    ProfileCut = ProfileExt.cut(self.SubtractiveCoinY(p1,p2,p3,p4,H,B2X,k))
                    ProfileTemp  = ProfileCut.removeSplitter()    
                
                if obj.WidthCentered == True:
                    p1 = v(w,h,  L-Z2Y/2)
                    p2 = v(w+W,h,L+Z2Y/2)
                    p3 = v(w+W,h,L+Z2Y/2+ZC2)
                    p4 = v(w,h,  L+Z2Y/2+ZC2)
                    ProfileExt = ProfileTemp.fuse(p.extrude(v(0,0,L+Z2Y/2+ZC2)))
                    ProfileCut = ProfileExt.cut(self.SubtractiveCoinY(p1,p2,p3,p4,H,B2X,k))
                    ProfileTemp  = ProfileCut.removeSplitter()
   
             
            if B1Y:
                if obj.WidthCentered == False:          
                    p1 = v(w,h,0)
                    p2 = v(W+w,h,   -Z1Y)
                    p3 = v(W+w,h,   -ZC1)
                    p4 = v(w,h,     -ZC1)
                    ProfileExt = ProfileTemp.fuse(p.extrude(v(0,0,-ZC1)))
                    ProfileCut = ProfileExt.cut(self.SubtractiveCoinY(p1,p2,p3,p4,H,B1X,k))
                    ProfileTemp  = ProfileCut.removeSplitter()
                
                if obj.WidthCentered == True:
                    if B1Y>0:
                        p1 = v(w,h,      Z1Y/2)
                        p2 = v(w+W,h,   -Z1Y/2)
                        p3 = v(w+W,h,   -Z1Y/2-ZC1)
                        p4 = v(w,h,     -Z1Y/2-ZC1)
                    else:
                        p1 = v(w,h,     Z1Y/2)
                        p2 = v(w+W,h,   -Z1Y/2)
                        p3 = v(w+W,h,   Z1Y/2-ZC1)
                        p4 = v(w,h,     Z1Y/2-ZC1)
                    ProfileExt = ProfileTemp.fuse(p.extrude(v(0,0,-ZC1-Z1Y/2)))    
                    ProfileCut = ProfileExt.cut(self.SubtractiveCoinY(p1,p2,p3,p4,H,B1X,k))
                    ProfileTemp  = ProfileCut.removeSplitter()
                    
            
            if B2X and not B2Y:
                if obj.WidthCentered == False:  
                    p1 = v(w,   h,     L)
                    p2 = v(W+w, H+h,   L+Z2X)
                    p3 = v(W+w, H+h,   L+ZC2)
                    p4 = v(w,   h,     L+ZC2)
                    ProfileExt = ProfileTemp.fuse(p.extrude(v(0,0,L+ZC2)))
                    ProfileCut = ProfileTemp.cut(self.SubtractiveCoinX(p1,p2,p3,p4,H,0,k))
                    ProfileTemp  = ProfileCut.removeSplitter()    
                
            if B1X and not B1Y:
                if obj.WidthCentered == False: 
                    p1 = v(w,   h,      0)
                    p2 = v(W+w, H+h,   -Z1X)
                    p3 = v(W+w, H+h,   -ZC1)
                    p4 = v(w,   h,     -ZC1)
                    ProfileExt = ProfileTemp.fuse(p.extrude(v(0,0,ZC1)))
                    ProfileCut = ProfileTemp.cut(self.SubtractiveCoinX(p1,p2,p3,p4,H,0,k))
                    ProfileTemp  = ProfileCut.removeSplitter()
            
          # if wire2: obj.Shape = Part.Compound([wire1,wire2])  # OCC Sweep doesn't be able hollow shape yet :-(
                
                
                
            obj.Shape = ProfileTemp  
        else:
            obj.Shape = Part.Face(wire1)
        obj.Placement = pl
        obj.positionBySupport()
       
   def SubtractiveCoinY(obj,p1,p2,p3,p4,l,A,k):
        FaceBevel = Part.Face(Part.makePolygon([p1,p2,p3,p4,p1]))
        coin1 = FaceBevel.extrude(v(0,k*l,0))
        coin2 = FaceBevel.extrude(v(0,-k*l,0))
        if A:
            coin1.rotate (p1,v(1,0,0),A)
            coin2.rotate (p1,v(1,0,0),A)
        fuse = coin1.fuse(coin2)
        return fuse
        
   def SubtractiveCoinX(obj,p1,p2,p3,p4,l,A,k):
        FaceBevel = Part.Face(Part.makePolygon([p1,p2,p3,p4,p1]))
        coin1 = FaceBevel.extrude(v(k*l,0,0))
        coin2 = FaceBevel.extrude(v(-k*l,0,0))
        if A:
            coin1.rotate (p1,v(0,1,0),A)
            coin2.rotate (p1,v(0,1,0),A)
        fuse = coin1.fuse(coin2)
        return fuse 
 
class SelObserver:
    def addSelection(self,doc,obj,sub,other):             
        form.update_selection(obj,sub)
        
    def clearSelection(self,other):   
        form.update_selection("","")
       

 
def recherche_fams():
    #Scan le fichier complet pour trouver les familles
    #Renvoie une liste contenant les noms
        tab =[]
        pos = 0 
        with open(path, "r") as file:
            while pos < file_len:
                # file.seek(pos)
                while True:
                    car = file.read(1)
                    if car == "*" or not car: break
                # print (pos)
                ligne = file.readline() #famille trouvée
             
                txt = ligne[:len(ligne)-1]  
                if txt: tab.append(txt)
                ligne = file.readline()
                ligne = file.readline()
                ligne = file.readline()
                pos = file.tell()
                txt =""
        return tab    

def trouve_txt(pos,txt):
    #Trouve un str à partir de pos
    #Renvoie la nouvelle position
    with open(path, "r") as file:
        file.seek(pos)
        while True:
            ligne = file.readline()
            if ligne.find(txt) !=-1 : break
        pos_line = file.tell() - len(ligne)      
        pos_found = pos_line + ligne.find(txt)
    return pos_found

def extrait_data(fam,size):
    #Extrait toutes les données pour une dimension d'une famille
    #Retour une liste:
    #Famille/Size/Donnée1/Donnée2...
    tab=[]
    tab.append(fam)
    tab.append(size)
    posfam = trouve_txt(0,fam)
    possize = trouve_txt(posfam,size)
    car=str=""
       
    with open(path, "r") as file:    
        file.seek (possize+len(size))
        while True:   
            while True:
                car = file.read(1)
                if car == "\t" or car == "\n": break
                str += car
            if str: tab.append(str)
            str=""   
            if  car == "\n": break
    # print(tab)
    return tab 

def recherche_ind(fam,type):
    # Recherche l'indice de la donnée dans la famille
    pos1 = trouve_txt(0,fam)
    pos2 = trouve_txt(pos1+1,"*")
    pos3 = trouve_txt(pos2+1,"*")
    pos4 = trouve_txt(pos3+1,"*")
    typ = []
    
    with open(path, "r") as file:  
        file.seek(pos4)
        ligne = file.readline().rstrip()
        typ = ligne.split("/")
        ind = typ.index(type)+1
    return ind

def recherche_dims(fam):
    #Recherche de toutes les dimensions d'une famille
    #Et retourne une liste les contenant

    pos1 = trouve_txt(0,fam)
    pos2 = trouve_txt(pos1+1,"*")
    pos3 = trouve_txt(pos2+1,"*")
    pos4 = trouve_txt(pos3+1,"*")
    tab = []
    str = ""    
    with open(path, "r") as file:
        file.seek(pos4)
        ligne = file.readline()
        car = file.read(1)
        while car !="\n" and car !="":
            while car != "\t":
                str += car
                car = file.read(1)
            if str: tab.append(str)
            str="" 
            ligne = file.readline()
            car = file.read(1)
    # tab.sort()
    # print (tab)
    return tab
  
   
 
# get the path of the current python script
file = "Profiles.txt"    
macro_path = os.path.realpath(__file__)
path = os.path.realpath(__file__)     
path = os.path.dirname(path)          
path = os.path.join(path,file)         
file_len = os.stat(path).st_size
ind_def = 10
print ("file: ",file_len) 

doc = FreeCAD.activeDocument()
if doc == None: doc = FreeCAD.newDocument()


o = SelObserver()
FreeCADGui.Selection.addObserver(o)   

form = Box()
form.exec_()

FreeCADGui.Selection.removeObserver(o) 
