/**
 * This script expands all annotations by a certain radius in micron
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
 * Authors: Benjamin Rothé - EPFL - UPCDA Lab & ChatGPT
 * Reviewer: Rémy Dornier - EPFL - BIOP
 * Inception date: 2026-01-21
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