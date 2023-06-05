# importing libraries:
from maya import cmds
from maya import mel
from .. import dpBaseControlClass

# global variables to this module:    
CLASS_NAME = "Octagram"
TITLE = "m104_octagram"
DESCRIPTION = "m099_cvControlDesc"
ICON = "/Icons/dp_octagram.png"

DP_OCTAGRAM_VERSION = 1.3


class Octagram(dpBaseControlClass.ControlStartClass):
    def __init__(self, *args, **kwargs):
        #Add the needed parameter to the kwargs dict to be able to maintain the parameter order
        kwargs["CLASS_NAME"] = CLASS_NAME
        kwargs["TITLE"] = TITLE
        kwargs["DESCRIPTION"] = DESCRIPTION
        kwargs["ICON"] = ICON
        dpBaseControlClass.ControlStartClass.__init__(self, *args, **kwargs)
        # dependence module list:
        self.checkModuleList = ['dpSquare']
    
    
    def cvMain(self, useUI, cvID=None, cvName=CLASS_NAME+'_Ctrl', cvSize=1.0, cvDegree=1, cvDirection='+Y', cvRot=(0, 0, 0), cvAction=1, dpGuide=False, *args):
        """ The principal method to call all other methods in order to build the cvControl curve.
            Return the result: new control curve or the destination list depending of action.
        """
        # check modules integrity:
        checkResultList = self.dpUIinst.startGuideModules(self.controlsGuideDir, "check", None, checkModuleList=self.checkModuleList)
        if len(checkResultList) == 0:
            # call combine function:
            result = self.cvCreate(useUI, cvID, cvName, cvSize, cvDegree, cvDirection, cvRot, cvAction, dpGuide, True)
            return result
        else:
            # error checking modules in the folder:
            mel.eval('error \"'+ self.langDic[self.langName]['e001_GuideNotChecked'] +' - '+ (", ").join(checkResultList) +'\";')
    
    
    def generateCombineCurves(self, useUI, cvID, cvName, cvSize, cvDegree, cvDirection, *args):
        """ Combine controls in order to return it.
        """
        # load module instance
        squareInstance = self.dpUIinst.initExtraModule('dpSquare', self.controlsGuideDir)
        # creating curve shapes:
        curve1 = squareInstance.cvMain(False, cvID, cvName, cvSize, cvDegree)
        curve2 = squareInstance.cvMain(False, cvID, cvName, cvSize, cvDegree)
        cmds.setAttr(curve2+".rotateZ", 45)
        mainCurve = self.combineCurves([curve1, curve2])
        return mainCurve