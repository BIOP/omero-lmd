/**
 * This script expands all annotations by a certain radius in micron
 *
 * Author: Rémy Dornier, EPFL - PTBIOP & ChatGPT
 * Date: 2026-01-21
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
 * 
 */


/**********************
 * VARIABLES TO MODIFY
 *********************/
 
 
double expansion_um = 1.0      // Expansion distance in microns
boolean processSelectedOnly = false   // true = only selected annotations


 /***********************
 * BEGINNING OF THE SCRIPT
 ***********************/


// ------------------------------------------------------------
// IMAGE & CALIBRATION
// ------------------------------------------------------------
def imageData = getCurrentImageData()
def server = imageData.getServer()
def cal = server.getPixelCalibration()

if (!cal.hasPixelSizeMicrons()) {
    throw new IllegalArgumentException("Image is not calibrated in microns.")
}

double pixelSize = cal.getAveragedPixelSizeMicrons()
double expansion_px = expansion_um / pixelSize

println "Expansion distance: ${expansion_um} µm (${expansion_px} px)"

// ------------------------------------------------------------
// GET ANNOTATIONS
// ------------------------------------------------------------
println "Getting annotations..."
def annotations = processSelectedOnly ?
        getSelectedObjects().findAll { it instanceof PathAnnotationObject } :
        getAnnotationObjects()

if (annotations.isEmpty()) {
    println "No annotations found."
    return
}

// ------------------------------------------------------------
// PREPARE GEOMETRIES
// ------------------------------------------------------------
println "Preparing geometries..."
def geomMap = [:]
annotations.each { ann ->
    geomMap[ann] = GeometryTools.roiToGeometry(ann.getROI())
}

// Union of ALL original geometries (used as collision mask)
Geometry allOriginal = geomMap.values().inject(null) { acc, g ->
    acc == null ? g : acc.union(g)
}

// ------------------------------------------------------------
// EXPAND EACH ANNOTATION
// ------------------------------------------------------------
println "Expanding annotations..."
annotations.each { ann ->
    try{
        Geometry baseGeom = geomMap[ann]
    
        // Smooth outward buffer
        Geometry expanded = baseGeom.buffer(
                expansion_px,
                8,
                BufferParameters.CAP_ROUND
        )
    
        // Keep only the outward ring
        Geometry outwardRing = expanded.difference(baseGeom)
    
        // Block expansion into other annotations
        Geometry blocked = outwardRing.difference(
                allOriginal.difference(baseGeom)
        )
    
        // Final geometry
        Geometry finalGeom = baseGeom.union(blocked)
        
        // update the original union shape
        allOriginal = allOriginal.union(finalGeom)
    
        if (finalGeom.isEmpty()) {
            println "Skipping empty geometry for annotation"
            return
        }
    
        // Convert geometry back to ROI (CORRECT METHOD)
        def newROI = GeometryTools.geometryToROI(
                finalGeom,
                ann.getROI().getImagePlane()
        )
    
        ann.setROI(newROI)
        def currentName = ann.getName()
        if(currentName == null || currentName == "null")
            ann.setName("Expanded")
        else ann.setName(currentName + "_expanded")
        Logger.info("The annotation "+currentName+": ID "+ann.getID()+" has been expanded")
    }catch (Exception e) {
        Logger.error("The annotation "+ann.getName()+": ID "+ann.getID()+" cannot be expanded")
        Logger.error(e.toString())
        def currentName = ann.getName()
        if(currentName == null || currentName == "null")
            ann.setName("NOT expanded")
        else ann.setName(currentName + "_NOT_expanded")
    }
}

// ------------------------------------------------------------
// DONE
// ------------------------------------------------------------
fireHierarchyUpdate()
println "Expansion complete."


/**********************
 * IMPORTS
 *********************/
 
 
import qupath.lib.roi.GeometryTools
import qupath.lib.roi.interfaces.ROI
import qupath.lib.objects.PathAnnotationObject
import org.locationtech.jts.geom.Geometry
import org.locationtech.jts.operation.buffer.BufferParameters
