"""
Export_LMD_ROIs.py
Convert OMERO ROIs to a format readable by the Leica Micro-Dissection (LMD) microscope

Author : Rémy Dornier - EPFL - BIOP
Date : 2025-01-10
Version 1.0.0

-----------------------------------------------------------------------------
Copyright (c) 2026 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, BioImaging And Optics Platform (BIOP)
All rights reserved.

Licensed under the BSD-3-Clause License:
Redistribution and use in source and binary forms, with or without modification, are permitted provided 
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer 
   in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products 
    derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, 
BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-----------------------------------------------------------------------------

"""

import os
import omero
import math
import numpy as np
import shapely
from shapely.geometry.polygon import Polygon
import re
import uuid
import traceback
import pandas as pd
from omero.gateway import BlitzGateway
from matplotlib.patches import Rectangle, Ellipse
from lmd.lib import Collection
from pathlib import Path
from PyQt6.QtWidgets import QLineEdit, QLabel, QFileDialog, QPushButton, QMainWindow, QVBoxLayout, \
    QWidget, QApplication, QHBoxLayout, QSpinBox


FONT_SIZE = 'font-size: 14px'
DEFAULT_HOST = "omero-server.epfl.ch"
PORT = 4064


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # main window settings
        self.setWindowTitle("Export ROIs for LMD")
        self.setMinimumSize(400, 100)
        widgets = []
        main_layout = QVBoxLayout()

        # host fields
        host_layout = QHBoxLayout()
        host_label = QLabel("OMERO Host")
        host_label.setStyleSheet(FONT_SIZE)
        self.host = QLineEdit()
        self.host.setText(DEFAULT_HOST)
        self.host.setStyleSheet(FONT_SIZE)
        host_widget = QWidget()
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host)
        host_widget.setLayout(host_layout)
        widgets.append(host_widget)

        # username fields
        username_layout = QHBoxLayout()
        username_label = QLabel("Username")
        username_label.setStyleSheet(FONT_SIZE)
        self.username = QLineEdit()
        self.username.setStyleSheet(FONT_SIZE)
        username_widget = QWidget()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username)
        username_widget.setLayout(username_layout)
        widgets.append(username_widget)

        # password fields
        password_layout = QHBoxLayout()
        password_label = QLabel("Password")
        password_label.setStyleSheet(FONT_SIZE)
        self.password = QLineEdit()
        self.password.setStyleSheet(FONT_SIZE)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        password_widget = QWidget()
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password)
        password_widget.setLayout(password_layout)
        widgets.append(password_widget)

        # images ids fields
        image_ids_layout = QHBoxLayout()
        image_ids_label = QLabel("Image IDs (URL)")
        image_ids_label.setStyleSheet(FONT_SIZE)
        self.image_ids = QLineEdit()
        self.image_ids.setStyleSheet(FONT_SIZE)
        image_ids_widget = QWidget()
        image_ids_layout.addWidget(image_ids_label)
        image_ids_layout.addWidget(self.image_ids)
        image_ids_widget.setLayout(image_ids_layout)
        widgets.append(image_ids_widget)

        # folder fields
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Saving folder")
        folder_label.setStyleSheet(FONT_SIZE)
        self.folder = QLineEdit()
        self.folder.setStyleSheet(FONT_SIZE)
        folder_button = QPushButton(text="Choose")
        folder_button.clicked.connect(self.open_file_chooser)
        folder_button.setStyleSheet(FONT_SIZE)
        folder_widget = QWidget()
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder)
        folder_layout.addWidget(folder_button)
        folder_widget.setLayout(folder_layout)
        widgets.append(folder_widget)

        # tolerance
        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("Polygon simplification")
        tolerance_label.setStyleSheet(FONT_SIZE)
        self.tolerance = QSpinBox()
        self.tolerance.setStyleSheet(FONT_SIZE)
        self.tolerance.setRange(1, 100)
        self.tolerance.setValue(10)
        self.tolerance.setSingleStep(1)
        tolerance_widget = QWidget()
        tolerance_layout.addWidget(tolerance_label)
        tolerance_layout.addWidget(self.tolerance)
        tolerance_widget.setLayout(tolerance_layout)
        widgets.append(tolerance_widget)

        # buttons fields
        button_layout = QHBoxLayout()
        ok_button = QPushButton(text="OK")
        ok_button.setStyleSheet(FONT_SIZE)
        ok_button.clicked.connect(self.run_app)
        cancel_button = QPushButton(text="Cancel")
        cancel_button.setStyleSheet(FONT_SIZE)
        cancel_button.clicked.connect(self.close_app)
        button_widget = QWidget()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        button_widget.setLayout(button_layout)
        widgets.append(button_widget)

        # building the main GUI
        for w in widgets:
            main_layout.addWidget(w)

        widget = QWidget()
        widget.setLayout(main_layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

    def close_app(self):
        self.close()

    def run_app(self):
        username = self.username.text()
        password = self.password.text()
        host = self.host.text()
        ids = self.image_ids.text()
        folder = self.folder.text()
        tolerance = self.tolerance.value() / 10
        self.close()
        run_script(host, username, password, folder, ids, tolerance)

    def open_file_chooser(self):
        response = QFileDialog.getExistingDirectory(parent=self, caption="select a folder", directory=os.getcwd())
        self.folder.setText(str(response))


def run_script(host, username, password, saving_folder, images_url, tolerance):
    """
    Extract ROIs from OMERO and convert them to LMD-readable shapes via a xml file.

    Parameters
    ----------
    host: str
        OMERO host
    username: str
        OMERO username
    password: str
        OMERO password
    saving_folder: str
        Path to the folder where to save the xml files
    images_url: str
        OMERO URL of images to process
    tolerance: float
        tolerance for polygon simplification

    """

    # check that saving folder exists
    if not os.path.exists(saving_folder):
        print(f"ERROR: Folder '{saving_folder}' does not exist.")
        return

    conn = BlitzGateway(username, password, host=host, port=PORT, secure=True)
    conn.connect()

    if conn.isConnected():
        print(f"Connected to {host}")
        try:
            conn.SERVICE_OPTS.setOmeroGroup(-1)
            roi_service = conn.getRoiService()
            ids = parse_omero_url(images_url)
            print(f"List of images to process: {ids}")
            for image_id in ids:
                image_wrapper = conn.getObject("Image", image_id)
                image_name = image_wrapper.getName()
                print(f"**** Working on image '{image_name}':{image_id} ****")
                print(f"Extracting ROIs...")
                result = roi_service.findByImage(image_id, None, conn.SERVICE_OPTS)

                print(f"Extracting Measurements...")
                measurement_file_path = download_measurements_file(image_wrapper)
                if not os.path.exists(measurement_file_path):
                    print(f"ERROR: Measurement file does not exist for image '{image_id}': {image_name}. "
                          f"Current path is {measurement_file_path}")
                    continue

                roi_df = pd.read_csv(measurement_file_path)

                shapes_dict = {}
                calibration_points = []
                n_rect, n_ellipse, n_line, n_point, n_poly, global_idx = 0, 0, 0, 0, 0, 0

                print(f"Filtering shapes with max area...")
                # filter only one shape per complex roi i.e. the one with maximum area
                roi_dict = filter_max_area_rois(result)

                # convert omero shapes to list of points
                # extract calibration points
                print(f"Converting omero shapes to lmd-readable shapes...")
                for shape_id, s in roi_dict.items() :
                    # retrieve information about the current shape
                    row_df = roi_df[roi_df["Object ID"] == shape_id]

                    # read LMD well from the table
                    if row_df["Well ID"].isnull().values.any() or row_df["Well ID"].empty:
                        # if the well ID of a cutting region is not defined or if the shape is not listed in the
                        # csv table, skip the shape
                        if type(s) != omero.model.PointI:
                            print(f"WARNING: Shape {shape_id} : {s.getTextValue().getValue()}")
                            print("WARNING: The current shape is not a calibration point and has no well ID.")
                            print("WARNING: This shape WILL BE IGNORED and will NOT BE INCLUDED in the final xml file.")
                            continue
                        well_id = ""
                    else:
                        well_id = row_df["Well ID"].item()

                    # read LMD batch from the table
                    if row_df["Batch ID"].isnull().values.any() or row_df["Batch ID"].empty:
                        batch_id = 1
                    else:
                        batch_id = int(row_df["Batch ID"].item())

                    # read QuPath ROI name from the table
                    if row_df["Name"].isnull().values.any() or row_df["Name"].empty:
                        shape_name = ""
                    else:
                        shape_name = row_df["Name"].item()

                    # read QuPath ROI class from the table
                    if row_df["Classification"].isnull().values.any() or row_df["Classification"].empty:
                        classification = ""
                    else:
                        classification = row_df["Classification"].item()

                    # select the right batch
                    if batch_id in shapes_dict:
                        shapes = shapes_dict[batch_id]
                    else:
                        shapes = []

                    # convert shapes to generic path and prepare LMD fields
                    path_list, s_rect, s_ellipse, s_line, s_point, s_poly = compute_shape_path(s, well_id, shape_name,
                                                                                               classification,
                                                                                               global_idx, tolerance)
                    n_rect += s_rect
                    n_ellipse += s_ellipse
                    n_line += s_line
                    n_point += s_point
                    n_poly += s_poly

                    # fill-in the list of shapes
                    if type(s) == omero.model.PointI:
                        calibration_points.append(path_list)
                    else:
                        shapes.append(path_list)

                    global_idx = n_rect + n_line + n_poly + n_ellipse
                    shapes_dict[batch_id] = shapes

                print(f"Converted {n_rect} rectangle(s), {n_ellipse} ellipse(s), {n_line} line(s), "
                      f"{n_point} point(s), {n_poly} polygone(s)/polyline(s)")

                # create LMD shapes from path
                print(f"Creating LMD calibration points...")
                calibration_points = [point[0] for point in sorted(calibration_points, key=lambda x:x[1])]

                # create and save LMD shapes in xml format
                for batch_id, shapes in shapes_dict.items():
                    save_lmd_shapes(calibration_points, shapes, image_id, image_name, batch_id, saving_folder)

                # delete the measurement file for the current image
                if os.path.exists(measurement_file_path):
                    print(f"Deleting measurement file from: {measurement_file_path}...")
                    os.remove(measurement_file_path)
                    print(f"Deleted !")

        except Exception as e:
            print(e)
            traceback.print_exc()

        finally:
            conn.close()
            print(f"Disconnected from {host}")


def compute_shape_path(s, well_id, shape_name, classification, global_idx, tolerance):
    """
    From the OMERO shape, compute the generic object path and send back LMD information i.e.
        - well ID
        - unique ID, which will be used in the transferID field of the microscope

    Parameters
    ----------
    s: ShapeData
        the current OMERO shape
    well_id: str
        ID of the well where to cut the shape at microscope
    shape_name: str
        QuPath name of the shape
    classification: str
        QuPath class of the shape
    global_idx: int
        unique LMD index of the shape
    tolerance: float
        tolerance for polygon simplification

    Returns
    -------
        list:
            attributes of the converted shape (path, unique LMD ID, well ID)
        n_x: int
            1 if the shape is of type x ; 0 otherwise
    """
    n_rect, n_ellipse, n_line, n_point, n_poly = 0, 0, 0, 0, 0
    path_list = []

    # check the geometry and convert to path
    if type(s) == omero.model.RectangleI:
        n_rect += 1
        x = s.getX().getValue()
        y = s.getY().getValue()
        width = s.getWidth().getValue()
        height = s.getHeight().getValue()
        rectangle = Rectangle((x, y), width, height)
        rectangle_path = convert_to_path(rectangle)
        unique_name = f"{well_id}_{shape_name}_{classification}_{global_idx}"
        path_list = [rectangle_path, well_id, unique_name]
    elif type(s) == omero.model.EllipseI:
        n_ellipse +=  1
        x = s.getX().getValue()
        y = s.getY().getValue()
        radiusX = s.getRadiusX().getValue()
        radiusY = s.getRadiusY().getValue()
        ellipse = Ellipse((x, y), radiusX * 2, radiusY * 2)
        ellipse_path = convert_to_path(ellipse)
        unique_name = f"{well_id}_{shape_name}_{classification}_{global_idx}"
        path_list = [ellipse_path, well_id, unique_name]
    elif type(s) == omero.model.PointI:
        n_point += 1
        x = s.getX().getValue()
        y = s.getY().getValue()
        point = [x, y]
        if shape_name == "":
            shape_name = get_shape_name(s.getTextValue())
        if shape_name == "":
            shape_name = "1"
        path_list = [point, shape_name]
    elif type(s) == omero.model.LineI:
        n_line += 1
        x1 = s.getX1().getValue()
        x2 = s.getX2().getValue()
        y1 = s.getY1().getValue()
        y2 = s.getY2().getValue()
        line_path = [[x1, y1], [x2, y2]]
        unique_name = f"{well_id}_{shape_name}_{classification}_{global_idx}"
        path_list = [line_path, well_id, unique_name]
    elif type(s) in [omero.model.PolygonI, omero.model.PolylineI]:
        n_poly += 1
        points = s.getPoints().getValue()
        polygon_path = []
        for coords in points.split():
            coord = coords.split(",")
            coord = [float(c) for c in coord]
            polygon_path.append(coord)

        simplified_polygon = shapely.simplify(Polygon(polygon_path), tolerance=tolerance, preserve_topology=True)
        polygon_path = np.array(simplified_polygon.boundary.coords).tolist()

        # Close the shape
        if type(s) == omero.model.PolygonI:
            polygon_path.append(polygon_path[0])

        unique_name = f"{well_id}_{shape_name}_{classification}_{global_idx}"
        path_list = [polygon_path, well_id, unique_name]

    return path_list, n_rect, n_ellipse, n_line, n_point, n_poly


def save_lmd_shapes(calibration_points, shapes, image_id, image_name, batch_id, saving_folder):
    """
    Convert generic path to LMD shapes, including calibration points, and save them in a xml file.
    The overview of the entire FoV, with shapes on top, is also saved as PNG file.

    Parameters
    ----------
    calibration_points: list
        the three points to calibrate the microscope
    shapes: list
        shapes to convert for the current batch
    image_id: int
        OMERO ID of the image
    image_name: str
        OMERO name of the image
    batch_id: int
        current ID of the batch
    saving_folder: str
        path to the user-defined folder where to save results

    Returns
    -------

    """
    print(f"Creating LMD shapes for batch {batch_id}...")
    shape_collection = Collection(calibration_points=np.array(calibration_points))

    for shape in shapes:
        shape_collection.new_shape(np.array(shape[0]), well=shape[1], TransferID=shape[2])

    # save xml file
    result_folder = os.path.join(saving_folder, f"{image_id}_{image_name}", f"batch_{batch_id}")
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    print(f"Saving xml file in {result_folder}...")
    shape_collection.save(os.path.join(result_folder, f"{image_id}_{image_name}_batch_{batch_id}_LMD-shapes.xml"))
    shape_collection.plot(calibration=True,
                          save_name=os.path.join(result_folder,
                                                 f"{image_id}_{image_name}_batch_{batch_id}_LMD-shapes.png"))


def filter_max_area_rois(result):
    """
    Get the shape with maximum area, based on the current QuPath convention.
    If multiple ROIs on OMERO have the same QuPath unique ID in their comment,
    only the one with the max area will be kept

    Parameters
    ----------
    result: RoiResults OMERO object
        the ROIs loaded from the current image

    Returns
    -------
        dict:
            dict of QuPath shape ID vs OMERO shape
    """
    roi_dict = {}
    area_dict = {}
    for roi in result.rois:
        shapes = filter_max_area_shapes(roi.copyShapes())
        for s in shapes:
            shape_id = get_shape_id(s.getTextValue())
            if shape_id == "":
                shape_id = uuid.uuid4()
            area = compute_shape_area(s)

            # update the dict if the new area is > to current one, for the same QuPath shape ID
            if shape_id not in roi_dict:
                roi_dict[shape_id] = s
                area_dict[shape_id] = area
            else:
                current_area = area_dict[shape_id]
                if area > current_area:
                    roi_dict[shape_id] = s
                    area_dict[shape_id] = area
    return roi_dict


def filter_max_area_shapes(shapes):
    """
    Get the shape with maximum area
        - in case the ROI has only one shape, return the shape
        - in case the ROI has multiple shapes (i.e. from a Geometry ROI type in QuPath),
            - return the one with max area if there is at least one shape of type Rectangle, Ellipse or Polygon
            - return all the shapes if NO shapes are of type Rectangle, Ellipse nor Polygon

    Parameters
    ----------
    shapes: list
        the list of available shapes

    Returns
    -------
        list: the shape with the maximum area or all shapes if shapes have no area
    """

    if len(shapes) == 1:
        return [shapes[0]]
    else:
        max_area = 0
        final_shape = None
        for s in shapes:
            area = compute_shape_area(s)
            if area > max_area:
                final_shape = s
                max_area = area

        if final_shape is not None:
            return [final_shape]
        else:
            return shapes


def compute_shape_area(s):
    """
    Compute the area of a shape with type Rectangle, Ellipse or Polygon.
    Return an area of zero for shapes with any other type.

    Parameters
    ----------
    s: ShapeData
        the OMERO shape

    Returns
    -------
        float: the shape area
    """

    if type(s) == omero.model.RectangleI:
        width = s.getWidth().getValue()
        height = s.getHeight().getValue()
        area = width * height

    elif type(s) == omero.model.EllipseI:
        radiusX = s.getRadiusX().getValue()
        radiusY = s.getRadiusY().getValue()
        area = radiusX * radiusY * math.pi

    elif type(s) == omero.model.PolygonI:
        points = s.getPoints().getValue()
        x = []
        y = []
        for coords in points.split():
            coord = coords.split(",")
            coord = [float(c) for c in coord]
            x.append(coord[0])
            y.append(coord[1])
        # computed from https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    else:
        area = 0

    return area


def parse_omero_url(url: str):
    """
    Extract image OMERO IDs from the given URL.
    URL Example : https://localhost/webclient/?show=image-40959|image-40958

    Parameters
    ----------
    url: str
        the omero URL containing the list of images to process

    Returns
    -------
        The list of image ids
    """

    regex = "https:\/\/.*\/.*\/?show=(?P<images>image-.\d*.*)"
    regex2 = "image-(.\d*.*)"
    pattern = re.compile(regex)
    pattern2 = re.compile(regex2)
    ids = []
    for match in pattern.finditer(url):
        results = match.group("images")
        for image in results.split("|"):
            ids.append(int(pattern2.findall(image)[0]))

    return ids


def get_shape_name(comment):
    """
    Extract the id of the QuPath ROI from the ROI comment.

    Parameters
    ----------
    comment: str
        ROI comment from QuPath

    Returns
    -------
    name: str
        The id of the shape

    """
    name = ""
    if comment is not None:
        tokens = comment.getValue().split(":")
        name = tokens[-1]
        if name.lower() not in ["", "null", "noname"]:
            return name
        else:
            name = ""
    return name


def get_shape_id(comment):
    """
    Extract the id of the QuPath ROI from the ROI comment.

    Parameters
    ----------
    comment: str
        ROI comment from QuPath

    Returns
    -------
    shape_id: str
        The id of the shape

    """
    shape_id = ""
    if comment is not None:
        tokens = comment.getValue().split(":")
        if len(tokens) > 3:
            shape_id = tokens[2]
            if shape_id.lower() not in ["", "null", "noname"]:
                return shape_id
    return shape_id


def convert_to_path(plt_shape):
    """
    Convert a Matplotlib shape into a list of points (i.e. path)

    Parameters
    ----------
    plt_shape: matplotlib.patches shape
        The shape to transform

    Returns
    -------
        The list of points corresponding to the path of the given shape

    """
    # Get the path
    path = plt_shape.get_path()
    # Get the list of path codes
    codes = path.codes
    # Get the list of path vertices
    vertices = path.vertices.copy()
    # Transform the vertices so that they have the correct coordinates
    return plt_shape.get_patch_transform().transform(vertices)


def download_measurements_file(wrapper):
    """
    Download the csv file corresponding to ROI features from OMERO

    Parameters
    ----------
    wrapper: OMERO repository wrapper
        the image wrapper

    Returns
    -------
        The path to the downloaded csv file

    """
    file_path = ""
    downloads_path = str(Path.home() / "Downloads")
    for ann in wrapper.listAnnotations():
        if (ann.OMERO_TYPE == omero.model.FileAnnotationI and
                ann.getFile().getName().endswith(".csv") and
            (ann.getFile().getName().lower().startswith("qupath") or
            "qp annotation table" in ann.getFile().getName().lower())):
            print("File ID:", ann.getFile().getId(), ann.getFile().getName(), "Size:", ann.getFile().getSize())
            file_path = os.path.join(downloads_path, ann.getFile().getName())

            with open(str(file_path), 'wb') as f:
                print("Downloading file to", file_path, "...")
                for chunk in ann.getFileInChunks():
                    f.write(chunk)
            print("File downloaded!")
            break
    return file_path


if __name__ == "__main__":
    list_argv = []
    app = QApplication(list_argv)
    window = MainWindow()
    window.show()
    app.exec()
