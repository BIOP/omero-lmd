/**
 * This script compute the total area of annotation per class
 *  
 * Author: Rémy Dornier - PTBIOP
 * Date: 2026-08-18
 * Version: 1.0.0
 *
 * -----------------------------------------------------------------------------
 * Copyright (c) 2026 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, BioImaging And Optics Platform (BIOP)
 * All rights reserved.
 * 
 * Licensed under the BSD-3-Clause License:
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided 
 * that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer 
 *    in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products 
 *     derived from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, 
 * BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
 * IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
 * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * -----------------------------------------------------------------------------
 */
 

/**********************
 * VARIABLES TO MODIFY
 *********************/


def listOfClass = ["Class1","Class2"] // add 'null' for objects with no class


/***********************
 * BEGINNING OF THE SCRIPT
 ***********************/


// get pixel size to calibrate area
def px = getCurrentServer().getPixelCalibration().getAveragedPixelSize().doubleValue()
println "Working on image: "+getProjectEntry().getImageName()

listOfClass.each{currentClass ->
	
	// get the annotation of class 'currentClass'
    def annotations = getAnnotationObjects().findAll(e-> e.getPathClass().toString().equals(currentClass))
    
    // compute the total area
    def sumArea = 0
    annotations.each {
        sumArea += it.getROI().getArea()   
    }
    
    // calibrate the area
    sumArea = sumArea * px * px 
    println "Area for class "+currentClass + " is "+sumArea+" um^2"
}

println "End of the script"
return