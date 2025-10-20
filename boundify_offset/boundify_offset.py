# ======================================
# Krita Boundify Offset plug-in (GUI)
# ======================================
# Copyright (C) 2025 L.Sumireneko.M
# This program is free software: you can redistribute it and/or modify it under the 
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>. 

import os
import sys

import krita
try:
    if int(krita.qVersion().split('.')[0]) == 5:
        raise
    from PyQt6 import uic
    from PyQt6.QtCore import QEvent
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QSlider, QSpinBox, QPushButton, QColorDialog
    )
    from PyQt6.QtGui import QPalette
    from PyQt6.QtGui import QColor
except:
    from PyQt5 import uic
    from PyQt5.QtCore import QEvent
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QSlider, QSpinBox, QPushButton, QColorDialog
    )
    from PyQt5.QtGui import QPalette
    from PyQt5.QtGui import QColor

from krita import *




from . import boundify_main


params = {
    "mode": "outline",
    "debug_path": True,
    "ofs": 1.0,
    "mitl": 4.0,
    "fo_mode": False,
    "line_cap": "butt", # "butt,square,round,arrow,brush"
    "line_join": "miter", # "miter,bevel,round,"
    "delete_orig": False ,
    "taper_mode" : "none", # "none,linear,linear_a,organic,chain,gear,sawtooth,punk,fluffy,rough,dot_to_dot"
    "cap_a": "butt" ,# "butt","square","round","arrow","ribbon","brush","brush2","brush3","bell","sigma"
    "cap_b": "butt" ,# "butt","square","round","arrow","ribbon","brush","brush2","brush3","bell","sigma"
    "preview": True,
    "preview_id_prefix": "preview_shapes_" ,
    "factor": 50 ,
    "previewcolor": "#ff0000" ,
    "single_path": False ,
    "dash": "none", # "none","dynamic_dash","random_dash","round_dot_dash"
    "reverse": False ,
    "original": False ,
    "fillview": False ,
    "stamp_along": {
        'flg': False,
        'id': "",
        'original': "",
        'center'  : {'x':0,'y':0},
        'data'    : [],
        'abst'    : ""
    }

}


ac_color = "#CCCCCC"
is_dark = False
checkbox_map=cb_temp_texts=cb_default_texts=""
class boundify_offsetDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        global params,ac_color,is_dark,checkbox_map,cb_temp_texts,cb_default_texts
        params['mode'] = "offset"
        params['fo_mode'] = True

        # 1st time
        is_dark = is_ui_color_dark(self)
        ac_color = "#CCCCCC" if is_dark== True else "#111111"

        self.setWindowTitle("Boundify offset")
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.centralWidget = uic.loadUi( os.path.join(os.path.dirname(os.path.realpath(__file__)),"boundify_offset.ui"))
        
        # Temporary state（This dict can store preview-ID and various data for input field value）
        self.preview_state = {}

        # Layout setting
        layout = QVBoxLayout()
        layout.addWidget(self.centralWidget)
        self.setLayout(layout)

        # Reference crearly to widgets
        self.spinBoxOfs = self.findChild(QDoubleSpinBox, "spinBoxOfs")
        self.spinBoxMiterRate = self.findChild(QDoubleSpinBox, "spinBoxMiterRate")
        self.spinBoxFactor = self.findChild(QDoubleSpinBox, "spinBoxFactor")
        self.sliderFactor = self.findChild(QSlider, "sliderFactor")

        self.comboBoxCornerType = self.findChild(QComboBox, "comboBoxCornerType")
        m_corner_type=["miter","bevel","round"]
        self.comboBoxCornerType.addItems(m_corner_type)  # Add menu entries
        self.comboBoxCornerType.setCurrentIndex(m_corner_type.index(params["line_join"]))  # default

        """
        self.comboBoxCapType = self.findChild(QComboBox, "comboBoxCapType")
        m_cap_type=["butt","square","round","arrow","ribbon","brush","brush2","brush3","bell","sigma"]
        self.comboBoxCapType.addItems(m_cap_type)  # Add menu entries
        self.comboBoxCapType.setCurrentIndex(m_cap_type.index(params["line_cap"]))  # default
        """

        # cap_a ,cap_b, taper_mode
        self.comboBoxCapAType = self.findChild(QComboBox, "comboBoxCapAType")
        m_cap_a_type=["butt","square","round","arrow","ribbon","brush","brush2","brush3","bell","sigma"]
        self.comboBoxCapAType.addItems(m_cap_a_type)  # Add menu entries
        self.comboBoxCapAType.setCurrentIndex(m_cap_a_type.index(params["cap_a"]))  # default

        self.comboBoxTaperMode = self.findChild(QComboBox, "comboBoxTaperType")
        #m_cap_type=["none","linear","linear_a","organic","chain","gear","sawtooth","punk","fluffy","rough","dot_to_dot","round_dot_dash","dynamic_dash","random_dash"]
        #self.comboBoxTaperMode.addItems(m_cap_type)  # Add menu entries


        m_cap_type = ["none","linear","linear_a","__SEPARATOR__",
                    "organic","chain","gear","sawtooth","punk","fluffy","rough",
                    "__SEPARATOR__",
                    "round_dot_dash","dynamic_dash","random_dash","__SEPARATOR__","dot_to_dot",
                    "__SEPARATOR__","stamp_top_group"]


        for item in m_cap_type:
            if item == "__SEPARATOR__":
                self.comboBoxTaperMode.insertSeparator(self.comboBoxTaperMode.count())
            else:
                self.comboBoxTaperMode.addItem(item)

        self.comboBoxTaperMode.setCurrentIndex(m_cap_type.index(params["taper_mode"]))  # default

        self.comboBoxCapBType = self.findChild(QComboBox, "comboBoxCapBType")
        m_cap_b_type=["butt","square","round","arrow","ribbon","brush","brush2","brush3","bell","sigma"]
        self.comboBoxCapBType.addItems(m_cap_b_type)  # Add menu entries
        self.comboBoxCapBType.setCurrentIndex(m_cap_b_type.index(params["cap_b"]))  # default

        self.okButton = self.findChild(QPushButton, "okButton")
        self.okButton.setStyleSheet(f"padding:3px;border: 3px solid {ac_color}; font-weight: bold; font-size: 14px;border-radius: 4px;")
        self.okButton.setMinimumWidth(80)


        self.cancelButton = self.findChild(QPushButton, "cancelButton")
        self.checkBoxPreview = self.findChild(QCheckBox, "checkBoxPreview")
        self.checkBoxOriginal = self.findChild(QCheckBox, "checkBoxOriginal")
        self.checkBoxFillview = self.findChild(QCheckBox, "checkBoxFillview")
        self.checkBoxStroke = self.findChild(QCheckBox, "checkBoxStroke")
        self.checkBoxReverse = self.findChild(QCheckBox, "checkBoxReverse")
        self.checkBoxSinglepath = self.findChild(QCheckBox, "checkBoxSinglepath")
        self.prev_slider_value = 50

        # Connect to event
        self.spinBoxOfs.setValue(float(params["ofs"]))
        #self.spinBoxOfs.editingFinished.connect(lambda:  self.on_spin_value_changed("ofs", self.spinBoxOfs.value()))
        self.spinBoxOfs.valueChanged.connect(lambda value:  self.on_spin_value_changed("ofs", value))  # raltime

        self.spinBoxMiterRate.setValue(int(params["mitl"]))
        #self.spinBoxMiterRate.editingFinished.connect(lambda:  self.on_spin_value_changed("mitl", self.spinBoxMiterRate.value()))
        self.spinBoxMiterRate.valueChanged.connect(lambda value:  self.on_spin_value_changed("mitl", value))  # realtime


        # extra ui mapping for stamp
        checkbox_map = {
            'cb_fill': self.findChild(QCheckBox, "checkBoxFillview"),
            'cb_orig': self.findChild(QCheckBox, "checkBoxOriginal"),
            'cb_sigl': self.findChild(QCheckBox, "checkBoxSinglepath"),
        }
        
        # Replace texts（True）
        cb_temp_texts = {
            'cb_fill': "Opacity",
            'cb_orig': "Random size",
            'cb_sigl': "Order size",
        }
        
        # Default（False）
        cb_default_texts = {
            key: checkbox.text() for key, checkbox in checkbox_map.items()
        }

        # Update Spinbox -> Slider
        def update_slider_from_spinbox(value):

            # Refuse small value changePrevents updates triggered by minimal value changes
            delta = abs(self.sliderFactor.value() - int(value))
            if 2 <= delta <= 5:
                return
            
            # Shut out other signals
            self.sliderFactor.blockSignals(True)
            try:
                self.sliderFactor.setValue(int(value))
                self.on_spin_value_changed("factor", value)
            finally:
                self.sliderFactor.blockSignals(False)

        def update_spinbox_from_slider():
            value = float(self.sliderFactor.value())
            
            # Reset inputValue to 0 if not initialized when compared with last time.
            # And,refuse small value changePrevents updates triggered by minimal value changes

            prev = getattr(self, 'prev_slider_value', 0.0)
            delta = abs(prev - value)            
            if 2 <= delta <= 10:
                return

            self.spinBoxFactor.blockSignals(True)
            try:
                self.spinBoxFactor.setValue(value)
                self.on_spin_value_changed("factor", value)
            finally:
                self.spinBoxFactor.blockSignals(False)
        
            # Cache the previous value for comparison
            self.prev_slider_value = value
        
        # For Spinbox setting
        self.spinBoxFactor.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinBoxFactor.setValue(int(params["factor"]))
        # Update when editing finished
        self.spinBoxFactor.editingFinished.connect(
            lambda: self.on_spin_value_changed("factor", self.spinBoxFactor.value())
        )
        # Realtime spinBoxFacor update(with sliderFactor unpdate)
        self.spinBoxFactor.valueChanged.connect(update_slider_from_spinbox)
        
        # For Silder
        self.sliderFactor.setRange(0, 100) 
        self.sliderFactor.setValue(int(params["factor"]))
        self.sliderFactor.valueChanged.connect(
            lambda value: self.on_spin_value_changed("factor", value)
        )
        self.sliderFactor.sliderReleased.connect(update_spinbox_from_slider)


        self.comboBoxCornerType.currentTextChanged.connect(lambda text: self.on_value_changed("line_join", text))
        # self.comboBoxCapType.currentTextChanged.connect(lambda text: self.on_value_changed("line_cap", text))
        self.comboBoxCapAType.currentTextChanged.connect(lambda text: self.on_value_changed("cap_a", text))
        self.comboBoxTaperMode.currentTextChanged.connect(lambda text: self.on_value_changed("taper_mode", text))
        self.comboBoxCapBType.currentTextChanged.connect(lambda text: self.on_value_changed("cap_b", text))


        self.checkBoxPreview.setChecked(params["preview"])
        self.checkBoxPreview.stateChanged.connect(lambda _: self.on_value_changed("preview", self.checkBoxPreview.isChecked()))

        self.checkBoxOriginal.setChecked(params["original"])
        self.checkBoxOriginal.stateChanged.connect(lambda _: self.on_value_changed("original", self.checkBoxOriginal.isChecked()))

        self.checkBoxFillview.setChecked(params["fillview"])
        self.checkBoxFillview.stateChanged.connect(lambda _: self.on_value_changed("fillview", self.checkBoxFillview.isChecked()))

        self.checkBoxStroke.setChecked(params["debug_path"])
        self.checkBoxStroke.stateChanged.connect(lambda _: self.on_value_changed("debug_path", self.checkBoxStroke.isChecked()))

        self.checkBoxReverse.setChecked(params["reverse"])
        self.checkBoxReverse.stateChanged.connect(lambda _: self.on_value_changed("reverse", self.checkBoxReverse.isChecked()))

        self.checkBoxSinglepath.setChecked(params["single_path"])
        self.checkBoxSinglepath.stateChanged.connect(lambda _: self.on_value_changed("single_path", self.checkBoxSinglepath.isChecked()))



        self.cancelButton.clicked.connect(self.cancel_dialog)
        self.okButton.clicked.connect(self.ok_dialog)

        # Paramater initialize
        self.preview_state = params.copy() 
        self.initialized = False
        self.resize(self.sizeHint())


        # Color selection
        self.colorButton = self.findChild(QPushButton, "colorButton")
        self.colorButton.setFixedSize(30, 20)# w,h
        self.current_color = QColor(params['previewcolor'])  # red
        style = (
            f"""
            QPushButton {{
                background-color:#ff0000;
                border: 2px solid black;   /* Black border */
                padding: 1px;              /* padding */
            }}
            QPushButton::hover {{
                border: 2px solid white;   /* hover */
            }}
            """
        )
        self.colorButton.setStyleSheet(style)



        #self.update_button_color()
        self.colorButton.clicked.connect(self.select_color)

    # update_checkbox ui for stamp_top_group 
    def update_checkbox_labels(self ,mode):
        global checkbox_map,cb_temp_texts,cb_default_texts
        texts = cb_temp_texts if mode == "stamp_top_group" else cb_default_texts
        for key, checkbox in checkbox_map.items():
            checkbox.setText(texts[key])


    # For common UI change
    def on_value_changed(self ,key ,value):
        print(f"UI Changed: {key} = {value}")
        self.preview_state[key] = value  # Set a value for the corresponding key

        if key == "taper_mode":
            self.preview_state['factor'] = 50
            self.spinBoxFactor.setValue(int(50))
            self.update_checkbox_labels(value)# if value =="stamp_top_group" custom ui

        boundify_main.re_init(params['preview_id_prefix'])
        if self.preview_state['preview']==True:
            boundify_main.process_selected_shapes(self.preview_state)
            boundify_main.re_z_index(params['preview_id_prefix'],9999)




    # For spinbox UI change
    def on_spin_value_changed(self,key, value):
        self.preview_state[key] = value  # Set a value for the corresponding key
        boundify_main.re_init(params['preview_id_prefix'])
        if self.preview_state['preview']==True:
            boundify_main.process_selected_shapes(self.preview_state)


    def ok_dialog(self):
        p = params['preview_id_prefix']
        if self.preview_state['preview']==False:
            self.preview_state['preview']=True
            boundify_main.re_init(p)
            boundify_main.process_selected_shapes(self.preview_state)
            boundify_main.determine(p)
        else:
            boundify_main.determine(p)
        self.initialized = False
        self.accept()

    # close button
    def cancel_dialog(self):
        # Remove group(s) matching "preview_group"
        boundify_main.re_init(params['preview_id_prefix'])
        self.initialized = False
        boundify_main.deselectAll()# Avoid segfault 11 bug 
        self.reject()

    def closeEvent(self, event):
        reply = QMessageBox(self)
        reply.setWindowTitle("Confirm")
        reply.setText("Really close this dialog?")

        # Add custom buttons
        btn_ok = reply.addButton("Close", QMessageBox.AcceptRole)  # "Yes"
        btn_cancel = reply.addButton("Stay", QMessageBox.RejectRole)  # "No"

        # Get OK button,and change the font style
        for button in reply.findChildren(QPushButton):  # use "reply"
            if button.text() == "Close":  # Change "Close" not "OK"
                button.setStyleSheet(f"padding:3px;border: 3px solid {ac_color}; font-weight: bold; font-size: 14px;border-radius: 4px;")
        btn_ok.setMinimumWidth(80)

        reply.exec_()

        # Detect user's choice
        if reply.clickedButton() == btn_ok:
            boundify_main.re_init(params['preview_id_prefix'])
            self.initialized = False
            #self.deleteLater()
            boundify_main.deselectAll()# Avoid segfault 11 bug 
            super().closeEvent(event)
            event.accept()  # close
        else:
            self.initialized = False
            event.ignore()  # cancel



    def showEvent(self, event):
        """ Run the function when the dialog is first shown """
        super().showEvent(event)
        if not self.initialized:
            boundify_main.process_selected_shapes(self.preview_state) # auto 
            self.initialized = True  # Execute at once


    def changeEvent(self, event):
        global params,ac_color,is_dark
        if event.type() != QEvent.ActivationChange:
            # Basic process does expect ActivationChange event 
            super().changeEvent(event)
            return

        # Update when this dialog becomes active
        if self.isActiveWindow():

            is_dark = is_ui_color_dark(self)
            ac_color = "#CCCCCC" if is_dark== True else "#111111"

            if self.preview_state['preview']==True:
                boundify_main.re_init(params['preview_id_prefix'])
                boundify_main.process_selected_shapes(self.preview_state)
                boundify_main.re_z_index(params['preview_id_prefix'],9999)
                super().changeEvent(event)




    def select_color(self):
        color = QColorDialog.getColor(initial=self.current_color, parent=self)
        if color.isValid():
            self.current_color = color
            self.update_button_color()

    def update_button_color(self):
        hex_color = self.current_color.name()  # "#25658" like color format
        params['previewcolor'] = hex_color
        self.preview_state['previewcolor'] = hex_color
        style = (
            f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 2px solid black;   /* Black border */
                padding: 1px;              /* padding */
            }}
            QPushButton::hover {{
                border: 2px solid white;   /* hover */
            }}
            """
        )
        self.colorButton.setStyleSheet(style)
        self.on_value_changed('previewcolor' ,hex_color)#




def is_ui_color_dark(self):
    palette = QApplication.palette()
    bg_color = palette.color(QPalette.Window)

    brightness = (bg_color.red() * 299 + bg_color.green() * 587 + bg_color.blue() * 114) / 1000
    
    if brightness < 128:
        print("Dark theme detected");return True
    else:
        print("Light theme detected");return False


# Run with outline mode
def run_outline_command(self):
    params['mode'] = "outline"
    boundify_main.process_selected_shapes(params)
    boundify_main.determine(params['preview_id_prefix'])

class boundify_offset(Extension):

    def __init__(self, parent):
        # This is initialising the parent, always important when subclassing.
        super().__init__(parent)
        self.dialog = boundify_offsetDialog()
        boundify_main.parent_dialog = self.dialog

    def setup(self):
        #This runs only once when app is installed
        pass

    def createActions(self, window):
        action = window.createAction("Apply offset to path", "Boundify offset ...", "tools/scripts")
        action.triggered.connect(self.dialog.show)

        action_two = window.createAction("Apply autline to path", "Apply Outline (Shape)", "tools/scripts")
        action_two.triggered.connect(lambda: run_outline_command(self))


# And add the extension to Krita's list of extensions:
Krita.instance().addExtension(boundify_offset(Krita.instance())) 



