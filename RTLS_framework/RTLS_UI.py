######################################################## NOTE #######################################################
# Date : 2022-05-27 to 2022-06-30                                                                                   #
#                                                                                                                   #
# calculate ui borders, the layout is something like this:                                                          #
#        ________________________________                                                                           #
#       |___________TITLE BAR____________|   (title %)                                                              #
#       |                   | 1.GATEWAY  |       of                                                                 #
#       |                   |------------|       |                                                                  #
#       |                   |  2.BEACON  |       |                                                                  #
#       |                   |------------|       |                                                                  #
#       |        MAP        |  3.UPDATE  |       |                                                                  #
#       |                   |------------|       |                                                                  #
#       |                   |            |       |                                                                  #
#       |                   |   4.CTRL   |       |                                                                  #
#       |___________________|____________|       v                                                                  #
#                                                                                                                   #
#         (stats %)   of ---------------->                                                                          #
#####################################################################################################################

import math
import time
import random
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from numpy import nan_to_num

# pip3 install git+https://github.com/yjg30737/pyqt-translucent-full-loading-screen-thread.git --upgrade
from pyqt_translucent_full_loading_screen_thread import LoadingThread, LoadingTranslucentScreen

# Import Our defined function.
from RTLS_Utils import *


# Thread class for the overlay loading screen.
class LoadingInterface(LoadingThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def run(self):
        time.sleep(3)
        
        
# Handling mouse drag events.
class MovingObject(QGraphicsEllipseItem):
    def __init__(self, x, y, r,color):
        super().__init__(0, 0, r, r)
        self.setPos(x, y)
        self.setBrush(QColor(color))
        self.setAcceptHoverEvents(True)
    
    
    def mousePressEvent(self, event):
        pass
    
    
    # Override mouse movement events.
    def mouseMoveEvent(self, event):
        orig_cursor_positon = event.lastScenePos()
        updated_cursor_position = event.scenePos()
        orig_position = self.scenePos()

        updated_cursor_x = updated_cursor_position.x() - orig_cursor_positon.x() + orig_position.x()
        updated_cursor_y = updated_cursor_position.y() - orig_cursor_positon.y() + orig_position.y()
        self.setPos(QPointF(updated_cursor_x, updated_cursor_y))
        
        
    # Override mouseRelaseEvent.
    def mouseReleaseEvent(self, event):
        print('x: {0}, y : {1}'.format(self.pos().x(),self.pos().y()))


# Interactive User Interface Class.
# Receives the estimated location from RTLS_Broker.py.
class UserInterface(QMainWindow):
    def __init__(self, CopyList):
        super().__init__()
        
        # Save the received the beacon positions.
        self.CopyList = CopyList 
        
        # Create a timer to automatically call a function.
        self.update_timer = QTimer() 
        
        # Initialize the variables.
        self.btn_state =  0 
        
        # Size of pixmap size when first executed.
        self.origin_size = {"X": 930,"Y": 945}
        
        # Beacon table column.
        self.beacon_table_col = 1
        
        # X-axis, y-axis, number of beacons of pixmap when resize event.
        self.pixmap_resize_x, self.pixmap_resize_Y, self.beacon_cnt = 0, 0, 0 
        
        # Beacon MAC address, name, color, estimated positions in beacon table.
        self.beacon_mac, self.beacon_name, self.random_color, self.table_beacon_x, self.table_beacon_y = [], [], [], [], [] 
        
        # Display the clustered-text box.
        self.beacon_items, self.TypeName, self.beacontable_node_id, self.text_line = [], [], [], []
        
        # Save the (x, y) for writing gateway position in table.
        self.table_gw_x, self.table_gw_y =  [], []
        
        # Save the (x, y) for drawing gateway position in pixmap.
        self.origin_beacon_x, self.origin_beacon_y = [], []
        
        # Save the received the configulation set from the config_gateway.csv.
        self.gw_value = 0
        
        # Overlay loading screen.
        self.__initUi__()
        self.func_beacon_mac_append()
        self.start_gui()
        
    
    # Calling the loading thread.
    def __initUi__(self):
        self.__startLoadingThread()
        
        
    # Starting the loading thread.
    def __startLoadingThread(self):
        self.__loadingTranslucentScreen = LoadingTranslucentScreen(parent=self, description_text='Connecting')
        self.__loadingTranslucentScreen.setDescriptionLabelDirection('Right')
        self.__thread = LoadingInterface(loading_screen=self.__loadingTranslucentScreen)
        self.__thread.start()        
        
        
    # Starting the interactive user interface.
    def start_gui(self):
        widget = QWidget(self)
        ui_grid = QGridLayout(widget)
        
        # Set gird layout positions.
        ui_grid.addWidget(self.ImageLayout(),0, 0, 6, 1)
        ui_grid.addWidget(self.Logo(),0, 1, 1, 1)
        ui_grid.addWidget(self.GWTable(), 1, 1, 2, 1) 
        ui_grid.addWidget(self.BeaconTable(), 3, 1, 1, 1)
        ui_grid.addWidget(self.Controller(),4, 1, 1, 1)
        self.func_beacon_display() 
        
        # Set QWidget frame.
        self.setCentralWidget(widget)
        self.setWindowTitle('Multi-gateway-based livestock tracker software')
        self.setGeometry(0,0,1000,900) 
        self.showMaximized()
        
        
    # Display INTFLOW logo on the upper right corner side.
    def Logo(self):
        groupbox = QGroupBox()
        groupbox.setStyleSheet("border-style : none")
        
        logo = QPixmap('images\intflow.png')
        logo_img = QLabel()
        logo_img.setPixmap(logo)
        logo_img.setAlignment(Qt.AlignCenter)

        vbox = QVBoxLayout()
        vbox.addWidget(logo_img)
        groupbox.setLayout(vbox)
        return groupbox


    # Display real-time GW, and beacon positions.
    def ImageLayout(self):
        img_box = QGroupBox('Floor Layout and Node Locations')
        img_box.setFont(QFont('나눔스퀘어_ac', 9))
        img_box.setStyleSheet("color : black")
        
        
        # Read gateway configulation information from config_gateway.csv.
        self.gw_value = func_gateway_config("configs\config_gateway.csv")
        self.gw_area_x = int(self.gw_value[0][4])
        self.gw_area_y = int(self.gw_value[1][4])
        self.gw_address = self.gw_value[1]      
        self.gw_color = self.gw_value[3]
        indoor_size = (self.gw_area_x,self.gw_area_y)
        
        
        # Generate gateway position automatically.
        # <class 'list'> [(GW1), (GW2), (GW3), (GW4)]
        self.gateway_pos=[[0,0],[indoor_size[0],0],[indoor_size[0],indoor_size[1]],[0,indoor_size[1]]]
        self.nodemap = QPixmap('images/SNL_map.png').scaled(934,945)
        
        self.img_view = QGraphicsView(self)
        self.img_scene = QGraphicsScene()    
        self.img_scene.addPixmap(self.nodemap)
        
        # Display function of gateway positons.
        self.func_GW_Draw()
        
        self.img_view.setScene(self.img_scene)
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.img_view)

        img_box.setLayout(self.vbox)        
        
        return img_box    
    
    # Writing the beacon information such as Type, MAC address, estimated positions.
    def BeaconTable(self):
        beacon_table_box = QGroupBox('Beacon Table')
        beacon_table_box.setFont(QFont('나눔스퀘어_ac', 9))
        beacon_table_box.setStyleSheet("color : black;")
        
        # TableWidget-based beacon table frame.
        self.beacon_table = QTableWidget() 
        self.beacon_table.setColumnCount(5)
        self.beacon_table.setStyleSheet("Color : black;")
        self.beacon_table.showGrid()
        self.beacon_table.setAutoScroll(True)
        self.beacon_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.beacon_table.verticalHeader().setVisible(False)
        
        # Set the size of the header to match the size of the table.
        self.beacon_table.setHorizontalHeaderLabels(["Type", "Name", "Address", "( x , y )", "Color"])
        self.beacon_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Layout vbox and save the layout in groupbox.
        vbox = QVBoxLayout()
        vbox.addWidget(self.beacon_table)
        beacon_table_box.setLayout(vbox)

        return beacon_table_box
    
    # Writing the gateway information such as Type, MAC address, estimated positions.
    def GWTable(self):
        gw_table_box = QGroupBox('Gateway Table')
        gw_table_box.setFont(QFont('나눔스퀘어_ac', 9))
        gw_table_box.setStyleSheet("color : black;")
        
        # TableWidget-based beacon gateway table frame.
        self.GWTable = QTableWidget()
        self.GWTable.setRowCount(4)
        self.GWTable.setColumnCount(5)
        self.GWTable.setStyleSheet("Color : black")
        self.GWTable.showGrid()
        self.GWTable.setAutoScroll(True)
        self.GWTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Set the size of the header to match the size of the table.
        self.GWTable.setHorizontalHeaderLabels(["Type", "Name", "Address", "( x , y )", "Color"])
        self.GWTable.verticalHeader().setVisible(False)
        self.GWTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.GWTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table_item = [] 
        table_item.append([])
        
        # Save the positons to display in the gateway table.
        for i in range(len(self.gw_value[3])-1):
            # If the indices are 0 and 3, the x position is 0, so it is save through a conditional statement.
            if i == 0 or i == 3:
                self.table_gw_x.append(0)
            # The other indexes 1 and 2 save the value of area_x.
            else:
                self.table_gw_x.append(self.gw_area_x)
            # If the indices are 0 and 1, the y-position is 0, so it is save through a conditional statement.
            if i == 0 or i == 1:
                self.table_gw_y.append(0)
            # The other indices 2 and 3 save the value of area_y.
            else:
                self.table_gw_y.append(self.gw_area_y)
                
        # Set gateway information in table using loop statement.
        for i in range(len(self.gw_value[3])-1):
            for j in range(len(self.gw_value[3])-1):
                table_text = ["BLE 5.0 / WiFi IoT","GATEWAY "+str(j),self.gw_address[j],"( "+str(self.table_gw_x[j])+" , "+str(self.table_gw_y[j])+" )"]
                GW_Table_item = QTableWidgetItem() 
                GW_Table_item.setText(table_text[i])
                GW_Table_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.GWTable.setItem(j,i,GW_Table_item)

            gw_color = QLabel()
            gw_color.setStyleSheet("background-color:"+self.gw_color[i]) 
        
            colorWidget = QWidget(self)
            layoutColor = QHBoxLayout(colorWidget)
            layoutColor.addWidget(gw_color)
            colorWidget.setLayout(layoutColor)
            self.GWTable.setCellWidget(i,4,colorWidget)
            
        vbox = QVBoxLayout()
        vbox.addWidget(self.GWTable)        
        gw_table_box.setLayout(vbox)

        return gw_table_box

    # Display controller layout.
    def Controller(self):
        controller_box = QGroupBox('Controller')
        controller_box.setFont(QFont('나눔스퀘어_ac', 9))
        controller_box.setStyleSheet("color : blak; background-color :white")
        
        # Set gird layout positions.
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.func_update_window(),0,0)
        grid_layout.addWidget(self.func_resizing_groupbox(),1,0)
        grid_layout.addWidget(self.func_controller_btn(),2,0)
        controller_box.setFixedHeight(330)
        controller_box.setLayout(grid_layout)

        return controller_box
    
    # Display the controller buttons.
    def func_controller_btn(self):
        btn_box = QGroupBox('Controller Button')
        btn_box.setFont(QFont("나눔스퀘어_ac",9))
        btn_box.setStyleSheet("color : black; background-color :white")
        
        # Beacon add button.
        add_btn = QPushButton('ADD') 
        add_btn.setFont(QFont("나눔스퀘어_ac",12))
        add_btn.clicked.connect(self.func_addbtn)
        add_btn.clicked.connect(self.func_pop_up)
        add_btn.setStyleSheet("color: black;")
        add_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Beacon remove button.
        remove_btn = QPushButton('REMOVE') 
        remove_btn.setFont(QFont("나눔스퀘어_ac",12))
        remove_btn.clicked.connect(self.func_remove_beacon)
        remove_btn.setStyleSheet("color : black;")
        remove_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Beacon information display button.
        self.OnOff_btn = QPushButton("ON/OFF") 
        self.OnOff_btn.setFont(QFont("나눔스퀘어_ac",12))
        self.OnOff_btn.setStyleSheet("color : black;")
        self.OnOff_btn.setCheckable(True)
        self.OnOff_btn.clicked.connect(self.func_change_button)
        self.OnOff_btn.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        # Program exit button.
        exit_btn = QPushButton("EXIT")
        exit_btn.setFont(QFont("나눔스퀘어_ac",12))
        exit_btn.clicked.connect(QCoreApplication.instance().quit)
        exit_btn.setStyleSheet("color : red") 
        exit_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        vbox = QVBoxLayout()
        hbox = QHBoxLayout() 
        hbox.addWidget(self.OnOff_btn)
        hbox.addWidget(add_btn)
        hbox.addWidget(remove_btn)
        hbox.addWidget(exit_btn)
        
        vbox.addLayout(hbox)
        btn_box.setLayout(vbox)
        return btn_box
    
    # Popup that occurs when the maximum number of beacons is exceeded
    def func_pop_up(self):
        load_number = func_beacon_config("configs\config_beacon.csv")
        beacon_sample = len(load_number)
        beacon_cnt = len(self.beacon_mac)
        if (beacon_cnt >= beacon_sample):
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.NoIcon)
            msgBox.setText("모든 비콘을 사용하고 있습니다.")
            msgBox.exec_() 
            
    # Check the ON/OFF changing.
    def func_change_button(self):
        if self.OnOff_btn.isChecked():
            self.func_Display_On()
        else:
            self.func_Display_Off()
    
    # Display update period controller.
    def func_update_window(self):
        update_groupbox = QGroupBox("Update Setting")
        update_groupbox.setFixedHeight(100)
        update_groupbox.setFont(QFont("나눔스퀘어_ac",9))
        update_groupbox.setStyleSheet("color : black; background-color :white")
        period_label = QLabel("Period")
        self.period_value = QLabel("0.2")
        
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setSingleStep(8)
        self.slider.setTickInterval(10)
        self.slider.setValue(10) # slider default gw_value 10 
        self.func_update_time(float(self.slider.value()/50)) 
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setRange(0, 70)
        self.slider.valueChanged.connect(self.func_changed_slider)

        hbox = QHBoxLayout()
        hbox.addWidget(period_label)
        hbox.addWidget(self.slider)
        hbox.addWidget(self.period_value)
        update_groupbox.setLayout(hbox)
        return update_groupbox

    def func_changed_slider(self):
        self.slider_value = int(self.slider.value() / 10)
        self.float_value = 0
        
        if self.slider_value == 0: # 0 second
            self.func_update_time(self.slider_value)
        
        elif self.slider_value == 1:# 0.2 second update period
            self.float_value = float(self.slider_value/5)
            self.func_update_time(float(self.float_value))
        
        elif self.slider_value == 2: # 0.5 second update period
            self.float_value = float(self.slider_value/4)
            self.func_update_time(float(self.float_value))
        
        elif self.slider_value == 3: # 1초 second update period
            self.func_update_time(int(self.slider_value-2))
        
        elif self.slider_value == 4: # 2초 second update period
            self.func_update_time(int(self.slider_value-2))
        
        elif self.slider_value == 5: # 3초 second update period
            self.func_update_time(int(self.slider_value-2))
        
        elif self.slider_value == 6: # 5초 second update period
            self.func_update_time(int(self.slider_value-1))
        
        elif self.slider_value == 7: # 10second update period
            self.func_update_time(int(self.slider_value+3))
        
        if self.slider_value <3: # less 3
            self.period_value.setText(str(self.float_value))
        elif self.slider_value <6: # less 6
            self.period_value.setText(str(self.slider_value-2))
        elif self.slider_value == 6: # equal to 6
            self.period_value.setText(str(self.slider_value-1))
        elif self.slider_value == 7: # equal to 7
            self.period_value.setText(str(self.slider_value+3))
            

    # A function where update_period is automatically called by slider_value using a timer
    def func_update_time(self,slider_value):
        if slider_value > 0:
            self.update_timer.start(slider_value*1000)
            self.update_timer.timeout.connect(self.func_update_period)
        else:
            self.update_timer.stop()
    
    # Resizing 2D map function.
    def func_resizing_groupbox(self):
        resize_box = QGroupBox("Display Setting")
        resize_box.setFont(QFont('나눔스퀘어_ac', 9))
        resize_box.setStyleSheet("color : black; background-color : white")

        resize_box_width = QLabel("Width :  ")
        resize_box_height = QLabel("Height : ")
        self.resize_lineedit_X = QLineEdit()
        self.resize_lineedit_Y = QLineEdit()

        resize_box_width.setFixedSize(50,50)
        resize_box_height.setFixedSize(50,50)
        self.resize_lineedit_X.setFixedSize(150,30)
        self.resize_lineedit_Y.setFixedSize(150,30)
        self.resize_lineedit_X.mousePressEvent = self.func_mousePressEvent

        # resize button
        resize_btn_ok = QPushButton("OK")
        resize_btn_ok.setFont(QFont("나눔스퀘어_ac",12))
        resize_btn_ok.clicked.connect(self.func_resizing)
        resize_btn_ok.setStyleSheet("color : black;")
        resize_btn_ok.setFixedSize(110,50)
        
        # reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setFont(QFont("나눔스퀘어_ac",12))
        reset_btn.clicked.connect(self.func_reset)
        reset_btn.setStyleSheet("color : black;")
        reset_btn.setFixedSize(110,50)
        
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(resize_box_width)
        hbox.addStretch(1)
        hbox.addWidget(self.resize_lineedit_X)
        hbox.addStretch(4)
        hbox.addWidget(resize_box_height)
        hbox.addStretch(1)
        hbox.addWidget(self.resize_lineedit_Y)
        hbox.addStretch(6)
        hbox.addWidget(reset_btn)
        hbox.addStretch(1)
        hbox.addWidget(resize_btn_ok)
        vbox.addLayout(hbox)
        
        resize_box.setLayout(vbox)
        return resize_box
    
    # Delete the information in the textline displayed on the screen when the mouse is clicked.
    def func_mousePressEvent(self, event):
        self.resize_lineedit_X.clear()
        
    # beacon MAC Address save type of list
    def func_beacon_mac_append(self):
        path = "configs\config_beacon.csv"
        beacon_csv_loader = pd.read_csv(path, names =['Address'], header = None)
        self.beacon_mac = beacon_csv_loader['Address'].values.tolist()
    
    # Output the created beacon to the screen
    def func_beacon_display(self):
        for i in range(len(self.beacon_mac)):
            self.func_beacon_create()
    
    # A function to make the position variables of beacon in list form.
    def func_beacon_append(self):
        self.table_x = []
        self.table_y = []
        
        # Copy estimated beacon positions form the IPS.py
        self.estimated_X = self.CopyList[0]
        self.estimated_Y = self.CopyList[1]

        # Generate, and copy resize beacon position values.
        for i in range(len(self.beacon_mac)):
            self.origin_beacon_x.append(nan_to_num(self.estimated_X[i]) * 100)
            self.origin_beacon_y.append(nan_to_num(self.estimated_Y[i]) * 100)
            
        # Calcuate beacon position in area.
        for i in range(len(self.beacon_mac)):      
            self.table_x.append(round(nan_to_num(self.estimated_X[i]), 2)) # self.table_x말고 table_beacon_x 되는지 확인
            self.table_y.append(round(nan_to_num(self.estimated_Y[i]), 2))
                        
        # table
        self.table_beacon_x = self.table_x
        self.table_beacon_y = self.table_y
    
    # A function that draws a beacon on the display.
    def func_beacon_draw(self):
        try:
            beacon_img = QGraphicsEllipseItem()
            
            # Calling a function that stores the positions of the beacon as a list.
            self.func_beacon_append()
            
            # Get a random color in hexadecimal.
            self.random_color.append("#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])) # random color create

            if self.pixmap_resize_x == 0:
                # Output the beacon to the existing positions on the display.
                beacon_img.setRect(self.origin_beacon_x[self.beacon_cnt],self.origin_beacon_y[self.beacon_cnt], 10, 10)

            else:
                # Calculate the proportion of the resized amount and output the beacon on the display.
                beacon_img.setRect(self.origin_beacon_x[self.beacon_cnt]*(self.pixmap_resize_x/self.origin_size["X"]),
                    self.origin_beacon_y[self.beacon_cnt]*(self.pixmap_resize_Y/self.origin_size["Y"]), 10, 10)
            
            # Assign randomly obtained color to beacon.
            self.beacon_color = self.random_color[self.beacon_cnt]
            self.penColor = QColor(self.beacon_color)
            beacon_img.setBrush(self.penColor)
            beacon_img.setPen(QPen(self.penColor, 3))
            self.img_scene.addItem(beacon_img)
            self.beacon_items.append(beacon_img)
        except IndexError:
            pass

    # Function that displays information of beacon as text.
    def func_Display_On(self):
        try:
            # The button is not pressed.
            if self.btn_state == 0:
                
                # Loop as many beacon as created.
                for i in range(self.beacon_cnt):
                    text_box = QGraphicsRectItem()
                    
                    # In case of original screen.
                    if self.pixmap_resize_x == 0:
                        text_pos_x = self.origin_beacon_x[i]
                        text_pos_y = self.origin_beacon_y[i]    
                    # In case of changed screen.
                    else:
                        # beacon_coordinates_x, and beacon_coordinates_Y calculated as a percentage.
                        text_pos_x = self.origin_beacon_x[i] * (self.pixmap_resize_x/self.origin_size["X"])
                        text_pos_y = self.origin_beacon_y[i] * (self.pixmap_resize_Y/self.origin_size["Y"])  
                          
                    # Create a text box containing MAC_Address, coordinates in the calculated coordinate values.
                    beacon_name=self.img_scene.addText('MAC : {0}\nCoordinate : ({1}, {2}) '.format(str(self.beacon_mac[i]), str(self.table_beacon_x[i]), str(self.table_beacon_y[i])))                    
                    self.beacon_name.append(beacon_name)
                    
                    # Where we use the '+12' because hide the overwrap the beacon nodes.
                    self.beacon_name[i].setPos(int(text_pos_x) + 12, int(text_pos_y) + 12)
                    text_box.setRect(text_pos_x + 12,text_pos_y +12 ,135,30)

                    text_box.setPen(QPen(QColor(self.random_color[i]),1))
                    
                    self.text_line.append(text_box)
                    self.img_scene.addItem(text_box)
 
                # Button state pressed.
                self.btn_state = 1
                
            # The button is pressed.
            elif self.btn_state == 1:
                    # Since the button is pressed, the beacon information is added one by one.
                    text_box = QGraphicsRectItem()
                    
                    # In case of original screen.
                    if self.pixmap_resize_x == 0:
                        text_pos_x = self.origin_beacon_x[self.beacon_cnt]
                        text_pos_y = self.origin_beacon_y[self.beacon_cnt]
                        
                    # In case of resize screen.
                    else: 
                        # Coordinates_x and Coordinates_y after correction calculated as a percentage
                        text_pos_x = self.origin_beacon_x[self.beacon_cnt] * (self.pixmap_resize_x/self.origin_size["X"])
                        text_pos_y = self.origin_beacon_y[self.beacon_cnt] * (self.pixmap_resize_Y/self.origin_size["Y"])
                    
                    # Create a text box containing MAC_Address, coordinates in the calculated coordinate values
                    beacon_text=self.img_scene.addText('MAC : {0}\nCoordinate : ({1}, {2}) '.format(str(self.beacon_mac[self.beacon_cnt]),str(self.table_beacon_x[self.beacon_cnt]), str(self.table_beacon_y[self.beacon_cnt])))
                    self.beacon_name.append(beacon_text)
                    
                    # Where we use the '+12' because hide the overwrap the beacon nodes.
                    self.beacon_name[self.beacon_cnt].setPos(int(text_pos_x) + 12, int(text_pos_y) + 12) 
                    text_box.setRect(text_pos_x + 12, text_pos_y +12 ,135,30)  
                    text_box.setPen(QPen(QColor(self.random_color[self.beacon_cnt]),1))
                    self.text_line.append(text_box)
                    self.img_scene.addItem(text_box)
                 
        except IndexError:
            pass
        except RuntimeError:
            pass
        
    # Delete text from screen when button off is clicked.
    def func_Display_Off(self):
        try:
            # The button is pressed.
            if self.btn_state == 1:
                self.btn_state = 0
                
                # Loop as many as the number of created beacons.
                for i in range(int(self.beacon_cnt)):
                    self.func_Display_Off_undo() 
        except IndexError:
            self.btn_state = 0
    
    # Delete the text information of the beacon.
    def func_Display_Off_undo(self):
        try:
            # Delete variables stored in display textbox.
            beacon = self.beacon_name.pop()
            self.img_scene.removeItem(beacon)
            line = self.text_line.pop()
            self.img_scene.removeItem(line)
            del beacon
            del line
        except RuntimeError:
            pass
    
    # Function to find the length of gateway calculated by area.
    # For drawing the gateway positions in 2D-pixmap.
    def func_GW_image_distance(self):

        # When the area positions are smaller than the existing pixmap size.
        if (self.gw_area_x *100) <  self.origin_size["X"] or self.gw_area_y * 100 < self.origin_size["Y"]:
            
            # Save the positions of the gateway using a loop.
            for i in range(len(self.gw_value[3])-1):
                if i == 0 or i == 3:
                    self.gateway_pos[i][0] = 10
                else:
                    self.gateway_pos[i][0] = 900
                if i == 0 or i == 1:
                    self.gateway_pos[i][1] = 10
                else:
                    self.gateway_pos[i][1] = 900
        else:
            for i in range(len(self.gw_value[3])-1):
                if i == 0 or i == 3:
                    self.gateway_pos[i][0] = 10
                else:
                    self.gateway_pos[i][0] = 900
                if i == 0 or i == 1:
                    self.gateway_pos[i][1] = 10
                else:
                    self.gateway_pos[i][1] = 900
                    
    # Show gateway on screen.
    def func_GW_Draw(self):
        # Gateway gw_value read from csv file and store in new variable.
        self.func_GW_image_distance()
   
        # Loop output to 4 gateway screens.
        for i in range(len(self.gw_value[3])-1):
            gateway = MovingObject(int(self.gateway_pos[i][0]),int(self.gateway_pos[i][1]),20,self.gw_color[i])
            self.img_scene.addItem(gateway)


    # Delete the beacon information.
    def func_undo(self):
        item = self.beacon_items.pop()
        self.img_scene.removeItem(item)   
        origin_beacon_x = self.origin_beacon_x.pop() 
        origin_beacon_y = self.origin_beacon_y.pop() 
        beacon_area_x = self.table_beacon_x.pop()
        beacon_area_y = self.table_beacon_y.pop()
        self.beacon_cnt -=1
        
        del item
        del origin_beacon_x
        del origin_beacon_y
        del beacon_area_x
        del beacon_area_y
        
    # Delete beacon information.
    def func_remove_beacon(self):
        try:
            # Delete beacon information.
            self.func_undo()
            
            # Delete beacon information of textbox when clicking display button.
            if self.btn_state == 1:
                self.func_Display_Off_undo()
                
            # Col +1 for index management after deleting and deleting columns remaining in the table.
            self.beacon_table.removeRow(self.beacon_cnt)
            self.beacon_table_col -=2
            self.beacon_table.setRowCount(self.beacon_table_col)
            self.beacon_table_col +=1
        except IndexError:
            self.beacon_cnt=0
            
    # Beacon information generation function.
    def func_beacon_create(self):
        try:
            # Beacon screen output.
            self.func_beacon_draw()
            if self.table_beacon_x[self.beacon_cnt] > 0:
            # Beacon information generation.
                beacon_mac_address = QTableWidgetItem() 
                self.text = str(self.beacon_mac[self.beacon_cnt])
                beacon_mac_address.setText(self.text)
                beacon_mac_address.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.beacon_table.setRowCount(self.beacon_table_col)
                self.beacon_table.setItem(self.beacon_cnt,2,beacon_mac_address)
            
            # Original screen.
            beacon_coordinate = QTableWidgetItem()
    
            # Original coordinate X, Y.
            self.text = "( "+str(self.table_beacon_x[self.beacon_cnt])+" , "+str(self.table_beacon_y[self.beacon_cnt])+" )"
            beacon_coordinate.setText(self.text)
                        
            # Center the texts.
            beacon_coordinate.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                
            # Output to beacon table.
            self.beacon_table.setItem(self.beacon_cnt,3,beacon_coordinate)
           
            # Beacon Type information.
            beacon_type = QTableWidgetItem() 
            self.text = "BLE 5.0 / E8"
            beacon_type.setText(self.text)
            beacon_type.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.beacon_table.setItem(self.beacon_cnt,0,beacon_type)
            self.TypeName.append(self.text)
        
            # Beacon ID information.
            beacon_id = QTableWidgetItem() 
            self.text = "BEACON " + str(self.beacon_cnt)
            beacon_id.setText(self.text)
            beacon_id.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.beacon_table.setItem(self.beacon_cnt,1,beacon_id)
            self.beacontable_node_id.append(self.text)
        
            # Beacon Color information.
            beacon_table_color = QLabel()
            beacon_table_color.setStyleSheet("background-color:"+self.beacon_color)
                    
            colorWidget = QWidget(self)
            layoutColor = QHBoxLayout(colorWidget)
            layoutColor.addWidget(beacon_table_color)
            colorWidget.setLayout(layoutColor)
            self.beacon_table.setCellWidget(self.beacon_cnt,4,colorWidget)
            
            # The button pressed.
            if self.btn_state == 1:
                self.func_Display_On()
            self.beacon_cnt+=1
            self.beacon_table_col += 1
        except IndexError:
            pass
        
    # Show gateway information in screen scaled positions.
    def func_resize_gateway(self):
        
        # Gateway output in screen scaled positions.
        for i in range(len(self.gw_value[3])-1):
            resize_gw = MovingObject(int(math.ceil((self.gateway_pos[i][0])*(self.pixmap_resize_x/self.origin_size["X"]))),int(math.ceil((self.gateway_pos[i][1])*(self.pixmap_resize_Y/self.origin_size["Y"]))),20,self.gw_color[i])
            self.img_scene.addItem(resize_gw)

    # Regenerate the beacon with the positions calculated with the modified screen.
    def func_resize_draw(self):
        # Output the beacon with the positions calculated with the modified screen.
        for i in range(int(self.beacon_cnt)):
            resize_beacon = QGraphicsRectItem()
            resize_beacon.setRect(self.origin_beacon_x[i]*(self.pixmap_resize_x/self.origin_size["X"]),self.origin_beacon_y[i]*(self.pixmap_resize_Y/self.origin_size["Y"]), 10,10)
            self.beacon_color = self.random_color[i]
            self.penColor = QColor(self.beacon_color)
            resize_beacon.setBrush(self.penColor)
            resize_beacon.setPen(QPen(self.penColor,3 ))
            self.img_scene.addItem(resize_beacon)
            self.beacon_items.append(resize_beacon)
            
        # When a button is pressed on the original screen.
        if(self.btn_state == 1):
            self.func_resize_beacon_update()
             
    
    # Original beacon screen data remove.
    def func_resize_undo(self):
        beacon_item = self.beacon_items.pop()
        del beacon_item
        
    # Text information output of beacon in resized screen.
    def func_resize_beacon_update(self):
        try: 
            # Original size screen button pressed.
            if self.btn_state == 1:
                
                # Button state change.
                self.btn_state = 0
                
                # Original beacon coordinate information display delete.
                for i in range(int(self.beacon_cnt)):
                    self.func_Display_Off_undo()
        except IndexError:
            self.btn_state = 0
        
        # Resize beacon coordinate information display output.
        for i in range(self.beacon_cnt):
            resize_line = QGraphicsRectItem()
            
            # Coordinates_x, and Coordinates_y after correction calculated as a percentage
            text_pos_x = self.origin_beacon_x[i] * (self.pixmap_resize_x/self.origin_size["X"])
            text_pos_y = self.origin_beacon_y[i] * (self.pixmap_resize_Y/self.origin_size["Y"])
            beacon_name = self.img_scene.addText('MAC : {0}\nCoordinate : ({1}, {2}) '.format(str(self.beacon_mac[i]),str(self.table_beacon_x[i]), str(self.table_beacon_y[i])))
            self.beacon_name.append(beacon_name)
            self.beacon_name[i].setPos(text_pos_x,text_pos_y)
            resize_line.setRect(self.origin_beacon_x[i] * (self.pixmap_resize_x/self.origin_size["X"]), self.origin_beacon_y[i] * (self.pixmap_resize_Y/self.origin_size["Y"]),135,30)    
            resize_line.setPen(QPen(QColor(self.random_color[i]),1))
            self.text_line.append(resize_line)
            self.img_scene.addItem(resize_line)
            
        self.btn_state = 1
        
    # Resize screen function.
    def func_resizing(self):
        try:
            # Line edit information save.
            self.text_X = self.resize_lineedit_X.text()
            self.text_Y = self.resize_lineedit_Y.text()
            if (int(self.text_X) and int(self.text_Y) >= 500): 
                
                # # resize pixmap scaled.
                self.nodemap = QPixmap('images/SNL_map.png').scaled(int(self.text_X),int(self.text_Y))
                self.pixmap_resize_x = int(self.text_X)
                self.pixmap_resize_Y = int(self.text_Y)
                self.img_scene = QGraphicsScene()
                
                # Add a new pixmap to the img_scene.
                self.img_scene.addPixmap(self.nodemap)
        
                # Gateway output in resized screen.
                self.func_resize_gateway()
      
                # Original beacon screen data remove.
                for i in range(len(self.beacon_items)):
                    # Deletion of beacons on the old screen.
                    self.func_resize_undo()
                self.resize_lineedit_X.clear()
                self.resize_lineedit_Y.clear()
                
                # Regenerate as many beacons as the number of beacons with the modified coordinates after deletion.
                self.func_resize_draw()
                self.img_view.setScene(self.img_scene)
                self.vbox.addWidget(self.img_view)
            else:
                self.resize_lineedit_X.clear()
                self.resize_lineedit_Y.clear()
                pass
        except ValueError:
            pass
        
    def func_reset_gateway(self):
        # Gateway output in screen scaled coordinates.
        for i in range(4):
            reset_gw = MovingObject(int(self.gateway_pos[i][0]),int(self.gateway_pos[i][1]),20,self.gw_color[i])
            self.img_scene.addItem(reset_gw)
        
    def func_reset_draw(self):
        # Output the beacon with the coordinates calculated with the modified screen.
        for i in range(int(self.beacon_cnt)):
            reset_beacon = QGraphicsRectItem()
            reset_beacon.setRect(self.origin_size["X"],self.origin_size["Y"], 10,10)
            self.beacon_color = self.random_color[i]
            self.penColor = QColor(self.beacon_color)
            reset_beacon.setBrush(self.penColor)
            reset_beacon.setPen(QPen(self.penColor,3 ))
            self.img_scene.addItem(reset_beacon)
            self.beacon_items.append(reset_beacon)
            
        # When a button is pressed on the original screen.
        if(self.btn_state == 1):
            self.func_reset_beacon_update()

    def func_reset_beacon_update(self):
        try: 
            # Original size screen button pressed.
            if self.btn_state == 1:
                
                # Button state change.
                self.btn_state =0
                
                # Original beacon coordinate information display delete.
                for i in range(int(self.beacon_cnt)):
                    self.func_Display_Off_undo()
        except IndexError:
            self.btn_state =0
        
        # Resize beacon coordinate information display output.
        for i in range(self.beacon_cnt):
            reset_line = QGraphicsRectItem()
            
            # Position_x, and position_y after correction calculated as a percentage
            beacon_name = self.img_scene.addText('MAC : {0}\nCoordinate : ({1}, {2}) '.format(str(self.beacon_mac[i]),str(self.table_beacon_x[i]), str(self.table_beacon_y[i])))
            self.beacon_name.append(beacon_name)
            self.beacon_name[i].setPos(self.origin_size["X"], self.origin_size["Y"])
            reset_line.setRect(self.origin_size["X"], self.origin_size["Y"],135,30)    
            reset_line.setPen(QPen(QColor(self.random_color[i]),1))
            self.text_line.append(reset_line)
            self.img_scene.addItem(reset_line)
            
        self.btn_state = 1
     
    def func_reset(self):
        try:
            # In case of resizing.
            if self.pixmap_resize_x != 0:
                
                # Create a size pixmap of the original image.
                self.nodemap = QPixmap('images/SNL_map.png').scaled(self.origin_size["X"],self.origin_size["Y"])
                self.img_scene = QGraphicsScene()
                self.img_scene.addPixmap(self.nodemap)
                
                # Gateway output on the display as original gateway positions.
                self.func_reset_gateway()
                for i in range(len(self.beacon_items)):    
                    
                    # Deletion of beacons on the old screen.
                    self.func_resize_undo()
                    
                # Initialize the values of the resize x-axis and y-axis to 0.
                self.pixmap_resize_x = 0
                self.pixmap_resize_Y = 0
                
                # Outputs the calculated beacon with the positions of the original beacon.
                self.func_reset_draw()
                self.img_view.setScene(self.img_scene)
                self.vbox.addWidget(self.img_view)
        except ValueError:
            pass
        except RuntimeError:
            pass
    
    # A function that recalls the deleted beacon information.
    def func_addbtn(self):
        beacon_cnt = len(self.beacon_mac)    
        
        # Delete as many as the number of created beacons.
        for i in range(beacon_cnt):
            self.func_remove_beacon()
        
        # Save of self.beacon_items values.
        for i in  range(beacon_cnt):
            self.func_beacon_create()
    
    def func_update_period(self):
        item_len= len(self.beacon_mac)
    
        # Delete of self.beacon_items values.
        for i in range(item_len):
            self.func_remove_beacon()
        
        # Save of self.beacon_items values.
        for i in  range(item_len):
            self.func_beacon_create()