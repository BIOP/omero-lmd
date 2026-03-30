/**
 * This script rename annotations of a certain class with a unique ID.
 * The ID should correspond to the Well ID of the micro-dissection LMD microscope
 * used to laser cut the tissue around the annotations.
 *
 * -----------------------------------------------------------------------------
 * MIT License
 * 
 * Copyright (c) 2026 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, BioImaging And Optics Platform (BIOP)
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * -----------------------------------------------------------------------------
 *  
 * Author: Rémy Dornier - EPFL - BIOP
 * Inception date: 2026-01-15
 * 
 */
 

/**********************
 * VARIABLES TO MODIFY
 *********************/
 
def includeNoneClassObjects = false 
 
// Map of Well IDs vs class
// check the name of the wellID in GitLab
def mapWellClass = [
    //"null":"A", // for annotations with no class
    "LTL":"A1-1",
    "THP":"A2-1",
    "NCC":"A3-1",
    "DBA":"A4-1",
    "Other":"A1-2"
]
    

 /***********************
 * BEGINNING OF THE SCRIPT
 ***********************/
 

def annotations = getAnnotationObjects()

annotations.each { ann ->
    if(ann.getPathClass() != null || includeNoneClassObjects) {
        def annClass
        if(ann.getPathClass() == null) {
            annClass = "null"
        }else{
            annClass = ann.getPathClass().getName()
        }
        def classCounter = 0
        for (def className: mapWellClass.keySet()) {
            if(annClass.toLowerCase().contains(className.toLowerCase())) {
                def tokens = mapWellClass.get(className).split("-")
                ann.getMetadata().put("Well ID", tokens[0])
                
                // check the batch number. 
                // If only one batch, the user may put only the wellID
                if(tokens.length > 1){
                    ann.getMetadata().put("Batch ID", tokens[1])
                } else {
                    ann.getMetadata().put("Batch ID", "1")
                }
                break;
            }
            classCounter++
        }
        
        // check if the class has been added by the user in 'mapWellClass'. If not, display a warning
        if(classCounter == mapWellClass.size()) {
           Logger.warn("BE CAREFUL: the class '"+annClass+"' is not registered in 'mapWellClass'. No well assigned. "+
           "Please add this class in the map to assign annotations a well.")
           
           // reset values
           ann.getMetadata().put("Well ID", "")
           ann.getMetadata().put("Batch ID", "")
        }
    } else {
        // remove the well id and batch id for annotation without any class
        // if the user specifies to not include them
        ann.getMetadata().put("Well ID", "")
        ann.getMetadata().put("Batch ID", "")
    }
}

Logger.info("Naming done ! Well IDs have been assigned to annotations.")
return