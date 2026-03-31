/**
 * This script rename annotations of a certain class with a unique ID.
 * The ID should correspond to the Well ID of the micro-dissection LMD microscope
 * used to laser cut the tissue around the annotations.
 *
 * -----------------------------------------------------------------------------
 * Copyright (c) 2026 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, BioImaging And Optics Platform (BIOP)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 * 		http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
    "class1":"A1-1",
    "class2":"A2-1",
    "class3":"A3-1",
    "class4":"A4-1",
    "class5":"A1-2"
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