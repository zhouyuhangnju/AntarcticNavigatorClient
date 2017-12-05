# encoding:utf-8

import mtTkinter as tk
import tkFont
import tkMessageBox
import re
import os
import sys
import pickle
import win32api
import time

import numpy as np
import math

from collections import Counter
from datetime import datetime
from PIL import ImageTk, Image, ImageGrab

# hand-written modules of this project
from getpath import ModisMap
import send_mail
import get_email_zip
import unzipfile
from mailutil import getemailpsw
import clearfile

import ctypes
import win32gui
import ctypes.wintypes

class RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long),
                ('top', ctypes.c_long),
                ('right', ctypes.c_long),
                ('bottom', ctypes.c_long)]
    def __str__(self):
        return str((self.left, self.top, self.right, self.bottom))

class MainWindow(object):

    def __init__(self, master):
        self.modisimgfile = None
        self.model = None

        # value matrices
        self.modisimg = None
        self.costimg = None
        self.prob_mat = None
        self.lonlat_mat = None

        self.operation_file = None

        self.img_num = 0
        self.last_num = 1

        self.__init_models()

        # canvas variables
        self.modis_imtk = None
        self.modis_canvas = None
        self.cost_imtk = None
        self.cost_canvas = None

        # canvas item tags
        # modis_canvas's index is 0, 2, 4...
        # cost_canvas's index is 1, 3, 5...
        self.tag_graticule = []
        self.tag_path = []
        self.tag_operation_point = []
        self.tag_temp_point = None
        self.tag_start_point = None
        self.tag_end_point = None
        self.tag_left_point = None
        self.tag_right_point = None

        self.cost_tag_graticule = []
        self.cost_tag_path = []
        self.cost_tag_operation_point = []
        self.cost_tag_temp_point = None
        self.cost_tag_start_point = None
        self.cost_tag_end_point = None
        self.cost_tag_left_point = None
        self.cost_tag_right_point = None

        self.trace_tag_path = []
        self.trace_tag_operation_point = []
        self.trace_tag_temp_point = None
        self.trace_tag_start_point = None
        self.trace_tag_end_point = None

        # operation point variables
        self.pointFrame = None
        self.recent_op_points = []
        self.current_op_points = []

        # other variables
        self.path = []
        self.ice_weight = 0.0
        self.default_zoom_factor = 0.15
        self.zoom_factor= 1.0
        self.zoom_level = [0.025, 0.05, 0.1, 0.15, 0.2, 0.25, 0.375, 0.5, 1.0]   # final static

        self.zoom_factor_trace = 1.0
        self.zoom_level_trace = [0.5, 1.0, 1.5, 2.0]   # final static

        self.mouse_status = tk.IntVar()         # control var of b0, b1 and b2 (radiobutton group), domain{1, 2, 3}
        self.check_value = tk.IntVar()          # whether add operation points when generating path
        self.optimize_target = tk.StringVar()   # control var of om (optionmenu), domain{'', '最便捷路径', '路程与破冰'}

        # indicator variables
        self.is_gen_path = True
        self.is_send_sar = True
        self.is_add_op = True

        # UI setting
        basic_h, basic_w = 1080, 1920
        title_h = 40
        control_wid = 280
        image_size = 900
        cost_width = 680
        cost_height = 580
        trace_control_h = 64

        titleframe = tk.Frame(master, width=basic_w, height=title_h)
        titleframe.grid(row=0, column=0, padx=1, pady=2, sticky=tk.N)
        ft = tkFont.Font(size=26, weight=tkFont.BOLD)
        ltitle = tk.Label(titleframe, text='基于不充分信息机器学习技术的海冰现报和雪龙船航线指导系统', font=ft)
        ltitle.grid(row=0, column=0, padx=50, pady=7)

        contentframe = tk.Frame(master, width=basic_w, height=basic_h-title_h)
        contentframe.grid(row=1, column=0, padx=1, pady=2, sticky=tk.N)

        frame1 = tk.Frame(contentframe, width=control_wid, height=basic_h-title_h)
        frame2 = tk.Frame(contentframe, width=image_size, height=basic_h-title_h)
        frame3 = tk.Frame(contentframe, width=cost_width, height=basic_h-title_h)
        frame1.grid(row=0, column=0, padx=1, pady=2, sticky=tk.N)
        frame2.grid(row=0, column=1, padx=1, pady=2, sticky=tk.N)
        frame3.grid(row=0, column=2, padx=1, pady=2, sticky=tk.N)

        south_size = control_wid - 10
        frame_south = tk.Frame(frame1, width=south_size, height=south_size)
        frame_south.grid(row=0, column=0, padx=1, pady=10)
        frame_control = tk.Frame(frame1, width=control_wid, height=basic_h-title_h-south_size)
        frame_control.grid(row=1, column=0, rowspan=2, padx=1, pady=15)

        south_file = 'northpole.jpg'
        south_image = Image.open(south_file)
        south_image = south_image.resize((south_size, south_size))
        self.south_imtk = ImageTk.PhotoImage(south_image)
        south_canvas = tk.Canvas(frame_south, width=south_size, height=south_size, bg='grey')
        south_canvas.create_image(0, 0, image=self.south_imtk, anchor='nw')
        south_canvas.pack()

        frame_modis = tk.Frame(frame2, width=image_size, height=image_size)
        frame_info = tk.Frame(frame2, width=image_size, height=basic_h-title_h-image_size)
        frame_modis.grid(row=0, column=0, padx=2, pady=10)
        frame_info.grid(row=1, column=0, padx=2, pady=2)

        frame_cost = tk.Frame(frame3, width=cost_width, height=cost_height)
        frame_trace = tk.Frame(frame3, width=cost_width, height=basic_h-title_h-cost_height-trace_control_h)
        frame_trace_zoom = tk.Frame(frame3, width=cost_width, height=trace_control_h)

        frame_cost.grid(row=0, column=0, padx=2, pady=5)
        frame_trace.grid(row=1, column=0, padx=2, pady=2)
        frame_trace_zoom.grid(row=2, column=0, padx=2, pady=2, sticky=tk.E)

        frame_cost_up = tk.Frame(frame_cost, width=cost_width, height=cost_height-trace_control_h)
        frame_cost_up.grid(row=0, column=0)
        frame_cost_down = tk.Frame(frame_cost, width=cost_width, height=trace_control_h)
        frame_cost_down.grid(row=1, column=0)

        # b_cost = tk.Button(frame_cost_down, command=self.__event_canvas_press3, text='image')
        # b_cost.grid(row=0, column=0, padx=20)
        # b_slides = tk.Button(frame_cost_down, command=self.__event_canvas_press4, text='slides')
        # b_slides.grid(row=0, column=1)
        # b_prev = tk.Button(frame_cost_down, command=self.__event_canvas_press2, text='<-')
        # b_prev.grid(row=0, column=2)
        # b_next = tk.Button(frame_cost_down, command=self.__event_canvas_press1, text='->')
        # b_next.grid(row=0, column=3)
        b_movie1 = tk.Button(frame_cost_down, command=self.__event_canvas_press5, text='背景描述')
        b_movie1.grid(row=0, column=4, padx=20)
        b_movie2 = tk.Button(frame_cost_down, command=self.__event_canvas_press6, text='船长评价')
        b_movie2.grid(row=0, column=5, padx=20)

        trace_file = 'trace.jpg'
        self.trace_image = Image.open(trace_file)
        self.trace_imtk = ImageTk.PhotoImage(self.trace_image)
        trace_canvas = tk.Canvas(frame_trace, width=cost_width, height=basic_h-title_h-cost_height-trace_control_h, bg='grey')
        trace_canvas.create_image(0, 0, image=self.trace_imtk, anchor='nw')

        xbar = tk.Scrollbar(frame_trace, orient=tk.HORIZONTAL)
        xbar.config(command=trace_canvas.xview)
        xbar.pack(side=tk.BOTTOM, fill=tk.X)
        ybar = tk.Scrollbar(frame_trace)
        ybar.config(command=trace_canvas.yview)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)
        trace_canvas.config(scrollregion=trace_canvas.bbox(tk.ALL))
        trace_canvas.config(xscrollcommand=xbar.set)
        trace_canvas.config(yscrollcommand=ybar.set)
        trace_canvas.pack()

        self.trace_canvas = trace_canvas

        self.trace_canvas.bind("<ButtonPress-1>", self.__event_trace_press)
        self.trace_canvas.bind("<B1-Motion>", self.__event_trace_move)

        tb1 = tk.Button(frame_trace_zoom, text='-', width=2, command=self.__callback_tb1_zoomout)
        tb2 = tk.Button(frame_trace_zoom, text='+', width=2, command=self.__callback_tb2_zoomin)
        tb1.grid(row=0, column=0)
        tb2.grid(row=0, column=2)

        self.zoom_text_trace = tk.StringVar()
        self.zoom_text_trace.set('%d' % (self.zoom_factor_trace * 100) + '%')
        scale_label = tk.Label(frame_trace_zoom, textvariable = self.zoom_text_trace, width=6)
        scale_label.grid(row=0, column=1)

        # canvas to show modis image
        self.__init_modis_canvas(frame_modis, image_size)
        self.__init_cost_canvas(frame_cost_up, cost_height, trace_control_h)

        l1 = tk.Label(frame_control, text='起点经度')
        l2 = tk.Label(frame_control, text='起点纬度')
        l3 = tk.Label(frame_control, text='终点经度')
        l4 = tk.Label(frame_control, text='终点纬度')
        l1.grid(row=0, column=0, pady=10)
        l2.grid(row=1, column=0, pady=10)
        l3.grid(row=2, column=0, pady=10)
        l4.grid(row=3, column=0, pady=10)

        self.e1 = tk.Entry(frame_control, width=10)
        self.e2 = tk.Entry(frame_control, width=10)
        self.e3 = tk.Entry(frame_control, width=10)
        self.e4 = tk.Entry(frame_control, width=10)
        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        self.e4.grid(row=3, column=1)

        # self.e1.insert(0, '80.48')
        # self.e2.insert(0, '-60.66')
        self.__draw_start_point()

        # self.e3.insert(0, '75.76')
        # self.e4.insert(0, '-69.69')
        self.__draw_end_point()

        b_c = tk.Checkbutton(frame_control, text='是否', variable=self.check_value)
        b_c.grid(row=5, column=0, pady=10)
        b_p = tk.Radiobutton(frame_control, text="增加作业点", variable=self.mouse_status, value=3)
        b_p.grid(row=5, column=1)
        b_a = tk.Button(frame_control, command=self.__callback_adjust_point, text='↑↓')
        b_a.grid(row=5, column=2)

        l6 = tk.Label(frame_control, text='考虑因素')
        l6.grid(row=6, column=0, pady=10)

        option_list = ['最便捷路径', '路程与破冰']
        om = tk.OptionMenu(frame_control, self.optimize_target, *option_list, command=self.__callback_optionchange)   # callback to auto show/hide sc&sct
        om.config(width=7)
        om.grid(row=6, column=1)

        frame_temp = tk.Frame(frame_control)
        frame_temp.grid(row=7, column=0, columnspan=2)

        self.sc = tk.Scale(frame_temp, from_=0, to=4, resolution=0.01, width=11, length=105, orient=tk.HORIZONTAL)
        self.sct = tk.Label(frame_temp, text='更短路径 更少破冰', font=('Purisa', 9))
        self.sc.grid(row=0, column=1)
        self.sct.grid(row=1, column=1)
        self.sc.grid_remove()
        self.sct.grid_remove()
        self.b10 = tk.Button(frame_temp, text='-', command=self.__callback_b10_minus)
        self.b11 = tk.Button(frame_temp, text='+', command=self.__callback_b11_add)
        self.b10.grid(row=0, column=0)
        self.b11.grid(row=0, column=2)
        self.b10.grid_remove()
        self.b11.grid_remove()

        b7 = tk.Button(frame_control, command=self.__callback_b7_genpath, text='生成路径')
        b7.grid(row=9, column=0, pady=10)
        b_hp = tk.Button(frame_control, command=self.__callback_bhp_hidepath, text='隐藏路径')
        b_hp.grid(row=9, column=1, pady=10)

        b_print = tk.Button(frame_control, command=self.__callback_print_trace, text='打印路径')
        b_print.grid(row=10, column=0, columnspan=2, pady=10)

        b_sa = tk.Button(frame_control, command=self.__callback_sar_send, text='请求SAR图')
        b_sa.grid(row=11, column=0, columnspan=2, pady=10)

        b_re = tk.Button(frame_control, command=self.__update_files, text='更新')
        b_re.grid(row=12, column=0, columnspan=2, pady=10)

        b9 = tk.Button(frame_control, command=self.__callback_b9_reset, text='复位')
        b9.grid(row=13, column=0, columnspan=2, pady=10)

        self.message_var = tk.StringVar()
        self.message_var.set('')
        mess = tk.Message(frame_control, textvariable=self.message_var)
        mess.grid(row=14, column=0, columnspan=2, pady=10)

        b0 = tk.Radiobutton(frame_info, text="默认", variable=self.mouse_status, value=0)
        b1 = tk.Radiobutton(frame_info, text="设置起点", variable=self.mouse_status, value=1)
        b2 = tk.Radiobutton(frame_info, text="设置终点", variable=self.mouse_status, value=2)
        b4 = tk.Button(frame_info, text='显示/隐藏经纬网', command=self.__callback_b4_showhide_graticule)
        b5 = tk.Button(frame_info, text='-', width=2, command=self.__callback_b5_zoomout)
        b6 = tk.Button(frame_info, text='+', width=2, command=self.__callback_b6_zoomin)
        b0.grid(row=0, column=0)
        b1.grid(row=0, column=1)
        b2.grid(row=0, column=2)
        b4.grid(row=0, column=4)
        b5.grid(row=0, column=5)
        b6.grid(row=0, column=7)

        self.zoom_text = tk.StringVar()
        self.zoom_text.set('%d' % (self.zoom_factor * 100) + '%')
        scale_label = tk.Label(frame_info, textvariable = self.zoom_text, width=6)
        scale_label.grid(row=0, column=6)

        blank_label = tk.Label(frame_info, textvariable = "    ", width=70)
        blank_label.grid(row=0, column=8)

        # event bindings
        self.modis_canvas.bind("<Button-1>", self.__event_canvas_click)
        self.modis_canvas.bind("<B1-Motion>", self.__event_canvas_move)
        self.modis_canvas.bind("<Motion>", self.__event_canvas_motion)

        # self.cost_canvas.bind("<Button-1>", self.__event_canvas_click)
        # self.cost_canvas.bind("<B1-Motion>", self.__event_canvas_move)
        # self.cost_canvas.bind_all("<w>", self.__event_canvas_press1)        # next page
        # self.cost_canvas.bind_all("<q>", self.__event_canvas_press2)        # previous page
        # self.cost_canvas.bind_all("<a>", self.__event_canvas_press3)        # back to cost image
        # self.cost_canvas.bind_all("<s>", self.__event_canvas_press4)        # back to ppt page

        for e in [self.e1, self.e2, self.e3, self.e4]:
            e.bind('<FocusOut>', self.__event_entry_input)
            e.bind('<Return>', self.__event_entry_input)
            e.bind('<Leave>', self.__event_entry_input)

        self.__rescale(self.default_zoom_factor)

        try:
            self.operation_file = open('data/operationpoints.txt')
            line = self.operation_file.readline()
            while line:
                # print line
                item = line.strip('\n').split('\t')
                lon = float(item[0])
                lat = float(item[1])
                self.recent_op_points.append((lon, lat))

                try:
                    i, j = self.__find_geocoordinates(lon, lat)
                except RuntimeError:
                    pass
                else:
                    self.current_op_points.append((lon, lat))
                    x, y = self.__matrixcoor2canvascoor(i, j)
                    cor = [x-5, y-5, x+5, y+5]
                    self.tag_operation_point.append(self.modis_canvas.create_oval(cor, fill='yellow'))
                    self.cost_tag_operation_point.append(self.cost_canvas.create_oval(cor, fill='yellow'))
                    i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
                    x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)
                    cor_trace = [x_trace-5, y_trace-5, x_trace+5, y_trace+5]
                    self.trace_tag_operation_point.append(self.trace_canvas.create_oval(cor_trace, fill='yellow'))

                line = self.operation_file.readline()
            self.operation_file.close()
        except:
            pass

        self.__draw_graticule()

        self.__auto_scrollbar_move()

    # load matrix files and init models
    def __init_models(self):
        datapath = 'data/'

        fs = os.listdir(datapath)
        jpgfiles = filter(lambda s: s.endswith('jpg'), fs)
        serials = map(lambda s: int(s.split('_')[0]), jpgfiles)
        latestjpgfile = jpgfiles[np.array(serials).argmax()]
        modisimgfile = datapath + latestjpgfile

        costimgfile = modisimgfile[0:-4] + '.cost'
        probfile = modisimgfile[0:-4] + '.prob'
        lonlatfile = modisimgfile[0:-4] + '.lonlat'
        icefile = modisimgfile[0:-4] + '.ice'

        # file existence
        if not os.path.isfile(modisimgfile) or not os.path.isfile(costimgfile) or not os.path.isfile(probfile) or not os.path.isfile(lonlatfile):
            return False

        self.modisimgfile = modisimgfile

        beta = 20

        fprob = open(probfile,'rb')
        flonlat = open(lonlatfile, 'rb')
        fice = open(icefile, 'rb')

        self.prob_mat = pickle.load(fprob)
        self.lonlat_mat = pickle.load(flonlat)
        self.ice_mat = pickle.load(fice)

        self.modisimg = Image.open(modisimgfile)
        self.modisimg = self.modisimg.crop((0, 0, (self.modisimg.width/beta)*beta, (self.modisimg.height/beta)*beta))   # divisible by beta

        self.costimg = Image.open(costimgfile)
        self.costimg = self.costimg.resize((int(self.prob_mat.shape[1] * beta), int(self.prob_mat.shape[0] * beta)))

        if self.modisimg.size[0] > 6000 or self.modisimg.size[1] > 6000:
            print 'Warning: current modis image file large than 6000*6000'

        if self.modisimg.size != self.costimg.size:
            self.__update_files()

        assert self.modisimg.size == self.costimg.size
        assert self.prob_mat.shape[0:2] == self.lonlat_mat.shape[0:2]
        assert self.prob_mat.shape[0] * beta  == self.modisimg.size[1]
        assert self.prob_mat.shape[1] * beta  == self.modisimg.size[0]

        # self.prob_mat = np.rot90(self.prob_mat)
        # self.lonlat_mat = np.rot90(self.lonlat_mat)
        # self.ice_mat = np.rot90(self.ice_mat)

        # self.modisimg = self.modisimg.transpose(Image.ROTATE_90)
        # self.costimg = self.costimg.transpose(Image.ROTATE_90)

        self.model = ModisMap(self.prob_mat)
        # print(self.modisimg.size)

        return True

    def __init_modis_canvas(self, frame, size):
        imtk = None
        imtk = ImageTk.PhotoImage(self.modisimg)
        self.modis_imtk = imtk
        canvas = tk.Canvas(frame, width=size, height=size, bg='grey')
        canvas.create_image(0, 0, image=imtk, anchor='nw')

        xbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        xbar.config(command=canvas.xview)
        xbar.pack(side=tk.BOTTOM, fill=tk.X)

        ybar = tk.Scrollbar(frame)
        ybar.config(command=canvas.yview)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.config(scrollregion=canvas.bbox(tk.ALL))
        canvas.config(xscrollcommand=xbar.set)
        canvas.config(yscrollcommand=ybar.set)
        canvas.pack()

        self.modis_canvas = canvas

    def __init_cost_canvas(self, frame, size, trace_control_h):
        # print(size)
        self.img_imtk = []
        self.cost_imtk = ImageTk.PhotoImage(self.costimg)
        self.img_imtk.append(self.cost_imtk)

        pptpath = 'ppt/'

        fs = os.listdir(pptpath)
        jpgfiles = filter(lambda s: s.endswith('JPG'), fs)
        for i in range(0, len(jpgfiles)):
            pptImage = Image.open(pptpath+jpgfiles[i])
            width, height = pptImage.size
            pptImage = pptImage.resize((width/24*17, height/24*17))
            self.img_imtk.append(ImageTk.PhotoImage(pptImage))

        # for i in range(0, len(self.img_imtk)):
        #     print(self.img_imtk[i])

        canvas = tk.Canvas(frame, width=size+100, height=size-trace_control_h-65, bg='grey')
        self.img_canvases = canvas.create_image(0, 0, image=self.img_imtk[self.img_num], anchor='nw')

        xbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        xbar.config(command=canvas.xview)
        xbar.pack(side=tk.BOTTOM, fill=tk.X)

        ybar = tk.Scrollbar(frame)
        ybar.config(command=canvas.yview)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.config(scrollregion=canvas.bbox(tk.ALL))
        canvas.config(xscrollcommand=xbar.set)
        canvas.config(yscrollcommand=ybar.set)
        canvas.pack()

        self.cost_canvas = canvas

    def __event_canvas_press1(self):

        # print self.img_num
        if self.img_num != 0:
            # next image
            self.img_num += 1

            # return to first image
            if self.img_num == len(self.img_imtk):
                self.img_num = 1

            # change image
            self.cost_canvas.itemconfig(self.img_canvases, image = self.img_imtk[self.img_num])
            self.cost_canvas.scan_dragto(0, 0, gain=1)

    def __event_canvas_press2(self):

        if self.img_num != 0:
            # previous image
            self.img_num -= 1

            # back to the last page
            if self.img_num == 0:
                self.img_num = len(self.img_imtk) - 1
                # self.__clear_cost_canvas()

            # change image
            self.cost_canvas.itemconfig(self.img_canvases, image = self.img_imtk[self.img_num])
            self.cost_canvas.scan_dragto(0, 0, gain=1)

    def __event_canvas_press3(self):
        # back to cost image
        if self.img_num != 0:
            self.last_num = self.img_num
            self.img_num = 0

            # change image
            self.cost_canvas.itemconfig(self.img_canvases, image = self.img_imtk[self.img_num])
            self.cost_canvas.scan_dragto(0, 0, gain=1)
            self.__auto_scrollbar_move()
            self.__draw_cost_canvas()


    def __event_canvas_press4(self):
        # back to ppt image
        if self.img_num == 0:
            self.img_num = self.last_num

            # change image
            self.__clear_cost_canvas()
            self.cost_canvas.itemconfig(self.img_canvases, image = self.img_imtk[self.img_num])
            # self.cost_canvas.scan_dragto(0, 0, gain=1)

            self.cost_canvas.xview_moveto(0)
            self.cost_canvas.yview_moveto(0)

    def __event_canvas_press5(self):
        win32api.ShellExecute(0, 'open', 'movie1.wmv', '',  '', 1)
        time.sleep(24)
        os.system('taskkill /F /IM wmplayer.exe')

    def __event_canvas_press6(self):
        win32api.ShellExecute(0, 'open', 'movie2.wmv', '', '', 1)
        time.sleep(55)
        os.system('taskkill /F /IM wmplayer.exe')

    def __draw_cost_canvas(self):
        self.__draw_operation_point()
        self.__draw_end_point()
        self.__draw_start_point()
        self.__draw_path()
        self.__draw_temp_point()
        if self.tag_graticule != []:
            self.__draw_graticule()
        try:
            self.__draw_left_point()
            self.__draw_right_point()
        except:
            pass

    def __clear_cost_canvas(self):
        if self.cost_tag_graticule != []:
            for i in range(0, len(self.cost_tag_graticule)):
                self.cost_canvas.delete(self.cost_tag_graticule[i])
            self.cost_tag_graticule = []
        if self.cost_tag_path != []:
            for i in range(0, len(self.cost_tag_path)):
                self.cost_canvas.delete(self.cost_tag_path[i])
            self.cost_tag_path = []
        if self.cost_tag_operation_point != []:
            for i in range(0, len(self.cost_tag_operation_point)):
                self.cost_canvas.delete(self.cost_tag_operation_point[i])
            self.cost_tag_operation_point = []
        if self.cost_tag_temp_point != None:
            self.cost_canvas.delete(self.cost_tag_temp_point)
            self.cost_tag_temp_point = None
        if self.cost_tag_start_point != None:
            self.cost_canvas.delete(self.cost_tag_start_point)
            self.cost_tag_start_point = None
        if self.cost_tag_end_point != None:
            self.cost_canvas.delete(self.cost_tag_end_point)
            self.cost_tag_end_point = None
        if self.cost_tag_left_point != None:
            self.cost_canvas.delete(self.cost_tag_left_point)
            self.cost_tag_left_point = None
        if self.cost_tag_right_point != None:
            self.cost_canvas.delete(self.cost_tag_right_point)
            self.cost_tag_right_point = None

    def __callback_tb1_zoomout(self):
        factor = self.zoom_factor_trace
        index = self.zoom_level_trace.index(factor)
        if index <= 0:
            return

        new_factor = self.zoom_level_trace[index - 1]
        self.__rescale_trace(new_factor)


    def __callback_tb2_zoomin(self):
        factor = self.zoom_factor_trace
        index = self.zoom_level_trace.index(factor)
        if index >= len(self.zoom_level_trace)-1:
            return

        new_factor = self.zoom_level_trace[index + 1]
        self.__rescale_trace(new_factor)

    def __callback_b4_showhide_graticule(self):

        if self.tag_graticule != []:
            #hide
            for i in xrange(0, len(self.tag_graticule)):
                self.modis_canvas.delete(self.tag_graticule[i])
            self.tag_graticule = []
            if self.cost_tag_graticule != []:
                for i in xrange(0, len(self.cost_tag_graticule)):
                    self.cost_canvas.delete(self.cost_tag_graticule[i])
                self.cost_tag_graticule = []
        else:
            #show
            self.__draw_graticule()


    def __callback_b5_zoomout(self):
        factor = self.zoom_factor
        index = self.zoom_level.index(factor)
        if index <= 0:
            return

        new_factor = self.zoom_level[index - 1]
        self.__rescale(new_factor)


    def __callback_b6_zoomin(self):
        factor = self.zoom_factor
        index = self.zoom_level.index(factor)
        if index >= len(self.zoom_level)-1:
            return

        new_factor = self.zoom_level[index + 1]
        self.__rescale(new_factor)

    def __callback_b7_genpath(self):
        # if not self.is_gen_path:
        #     tkMessageBox.showerror('Error', '存在不合法输入！')
        #     return

        mark2 = False
        if '' in [self.e1.get(), self.e2.get(), self.e3.get(), self.e4.get(), self.optimize_target.get()]:
            if len(self.current_op_points) >= 2:
                mark2 = True
            else:
                return

        start = (-1, -1)
        end = (-1, -1)
        if not mark2:
            slon, slat = self.__check_input(self.e1.get(),True), self.__check_input(self.e2.get(),False)
            elon, elat = self.__check_input(self.e3.get(),True), self.__check_input(self.e4.get(),False)     #RuntimeError

            start = self.__find_geocoordinates(slon, slat)
            end = self.__find_geocoordinates(elon, elat)

        ratio = -1.0    #cost = 0.01 + ratio*p(thick ice/cloud) + (1-ratio)*dist
        mark = 0
        target = self.optimize_target.get()
        if target == u'最便捷路径':
            mark = 0
        elif target == u'路程与破冰':
            mark = 1
            ratio = float(self.sc.get())

        t1 = datetime.now()

        cost = 0
        path = []

        print mark2
        print self.check_value.get()
        if (not mark2) and (self.check_value.get() == 0):
            cost, path = self.model.getpath(start, end, mark, ratio)
        else:
            single_p = []
            if not mark2:
                temp_end = self.__find_geocoordinates(self.current_op_points[0][0], self.current_op_points[0][1])
                temp_c, temp_p = self.model.getpath(start, temp_end, mark, ratio)
                cost = cost + temp_c
                single_p.append(temp_p)
            for i in range(len(self.current_op_points)-1):
                temp_start = self.__find_geocoordinates(self.current_op_points[i][0], self.current_op_points[i][1])
                temp_end = self.__find_geocoordinates(self.current_op_points[i+1][0], self.current_op_points[i+1][1])
                temp_c, temp_p = self.model.getpath(temp_start, temp_end, mark, ratio)
                cost = cost + temp_c
                single_p.append(temp_p)
            if not mark2:
                temp_start = self.__find_geocoordinates(self.current_op_points[-1][0], self.current_op_points[-1][1])
                temp_c, temp_p = self.model.getpath(temp_start, end, mark, ratio)
                cost = cost + temp_c
                single_p.append(temp_p)

            for i in range(len(single_p), 0, -1):
                path.extend(single_p[i-1])
            print path

        t2 = datetime.now()

        self.path = path
        self.__draw_path()
        self.modis_canvas.update_idletasks()
        self.cost_canvas.update_idletasks()
        self.mouse_status.set(0)

        print "=============================="
        print '  system:'
        print '    path generated'
        print '    '
        print '    from %s'%(self.e1.get() + ', ' + self.e2.get())
        print '    to   %s'%(self.e3.get() + ', ' + self.e4.get())
        print '    '
        print '    length: %d'%len(path)
        print '    cost  : %f'%cost
        print '    time  : %s'%str(t2-t1)
        print "==============================\n"
        sys.stdout.flush()

    def __callback_b9_reset(self):

        # clear entries
        for e in [self.e1, self.e2, self.e3, self.e4]:
            e.delete(0, 'end')

        # reset control variables
        self.optimize_target.set('')
        self.mouse_status.set(0)
        self.sc.set(0)
        self.path = []

        # clear canvas
        self.modis_canvas.delete("all")
        self.modis_canvas.create_image(0, 0, image=self.modis_imtk, anchor='nw')

        self.cost_canvas.delete("all")
        self.img_imtk = []
        self.img_imtk.append(self.cost_imtk)
        pptpath = 'ppt/'
        fs = os.listdir(pptpath)
        jpgfiles = filter(lambda s: s.endswith('JPG'), fs)
        for i in range(0, len(jpgfiles)):
            pptImage = Image.open(pptpath+jpgfiles[i])
            width, height = pptImage.size
            pptImage = pptImage.resize((width/24*17, height/24*17))
            self.img_imtk.append(ImageTk.PhotoImage(pptImage))
        self.img_canvases = self.cost_canvas.create_image(0, 0, image=self.img_imtk[self.img_num], anchor='nw')

        self.trace_canvas.delete("all")
        self.trace_canvas.create_image(0, 0, image=self.trace_imtk, anchor='nw')

        # for i in range(0, len(self.img_imtk)):
        #     print(self.img_imtk[i])
        # self.cost_canvas.create_image(0, 0, image=self.cost_imtk, anchor='nw')

        self.tag_operation_point = []
        self.cost_tag_operation_point = []
        self.trace_tag_operation_point = []

        self.current_op_points = []
        self.recent_op_points = []

        try:
            self.operation_file = open('data/operationpoints.txt')
            line = self.operation_file.readline()
            while line:
                # print line
                item = line.strip('\n').split('\t')
                lon = float(item[0])
                lat = float(item[1])
                self.recent_op_points.append((lon, lat))

                try:
                    i, j = self.__find_geocoordinates(lon, lat)
                except RuntimeError:
                    pass
                else:
                    self.current_op_points.append((lon, lat))
                    x, y = self.__matrixcoor2canvascoor(i, j)
                    cor = [x-5, y-5, x+5, y+5]
                    self.tag_operation_point.append(self.modis_canvas.create_oval(cor, fill='yellow'))
                    self.cost_tag_operation_point.append(self.cost_canvas.create_oval(cor, fill='yellow'))
                    i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
                    x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)
                    cor_trace = [x_trace-5, y_trace-5, x_trace+5, y_trace+5]
                    self.trace_tag_operation_point.append(self.trace_canvas.create_oval(cor_trace, fill='yellow'))

                line = self.operation_file.readline()
            self.operation_file.close()
        except:
            pass

        self.e1.insert(0, '80.48')
        self.e2.insert(0, '-60.66')
        self.__draw_start_point()

        self.e3.insert(0, '75.76')
        self.e4.insert(0, '-69.69')
        self.__draw_end_point()

        # clear canvas tags
        self.tag_graticule = []
        self.tag_start_point = None
        self.tag_end_point = None
        self.tag_temp_point = None
        self.tag_path = []

        self.cost_tag_graticule = []
        self.cost_tag_start_point = None
        self.cost_tag_end_point = None
        self.cost_tag_temp_point = None
        self.cost_tag_path = []

        self.__rescale(self.default_zoom_factor)

        self.__draw_graticule()

    def __callback_b10_minus(self):
        ratio = float(self.sc.get())
        if ratio == 0.0:
            tkMessageBox.showinfo("Info", "已达到最小值0.0，不可再减小！")
        else:
            ratio = ratio - 0.01
            self.sc.set(ratio)

    def __callback_b11_add(self):
        ratio = float(self.sc.get())
        if ratio == 4.0:
            tkMessageBox.showinfo("Info", "已达到最大值4.0，不可再增加！")
        else:
            ratio = ratio + 0.01
            self.sc.set(ratio)

    def __callback_bhp_hidepath(self):
        if self.tag_path != []:
            for i in xrange(0, len(self.tag_path)):
                self.modis_canvas.delete(self.tag_path[i])
            self.tag_path = []

        if self.cost_tag_path != []:
            for i in xrange(0, len(self.cost_tag_path)):
                self.cost_canvas.delete(self.cost_tag_path[i])
            self.cost_tag_path = []

        if self.trace_tag_path != []:
            for i in xrange(0, len(self.trace_tag_path)):
                self.trace_canvas.delete(self.trace_tag_path[i])
            self.trace_tag_path = []

    def __callback_print_trace(self):
        printname = 'print.jpg'

        # get current window
        rect = RECT()
        HWND = win32gui.GetForegroundWindow()
        ctypes.windll.user32.GetWindowRect(HWND,ctypes.byref(rect))
        rangle = (rect.left+2,rect.top+2,rect.right-2,rect.bottom-2)

        # grab picture and save
        pic = ImageGrab.grab(rangle)
        pic.save(printname)

        import printer
        printer.send_to_printer(printname)
        return

    def __callback_sar_send(self):
        # import webbrowser
        # url = 'https://www.asf.alaska.edu/sentinel/'
        # webbrowser.open(url)
        self.sarFrame = tk.Toplevel()
        self.sarFrame.geometry("500x200")
        self.sarFrame.resizable(width=False, height=False)
        self.sarFrame.title('Require SAR IMAGE')

        self.frame_receive = tk.Frame(self.sarFrame, width=500)
        self.frame_range = tk.Frame(self.sarFrame, width=500)
        self.frame_receive.pack()
        self.frame_range.pack()

        self.label_mail = tk.Label(self.frame_receive, text='收件人邮箱：')
        self.entry_mail = tk.Entry(self.frame_receive, width=45)
        self.label_mail.grid(row=0, column=0, pady=20)
        self.entry_mail.grid(row=0, column=1, pady=20)

        self.entry_mail.bind('<Tab>', self.__event_email_check)
        self.entry_mail.bind('<FocusOut>', self.__event_email_check)
        self.entry_mail.bind('<Return>', self.__event_email_check)
        self.entry_mail.bind('<Leave>', self.__event_email_check)

        self.label_leftlon = tk.Label(self.frame_range, text='左上角经度:')
        self.label_leftlon.grid(row=0, column=0, padx=5, pady=5)
        self.entry_leftlon = tk.Entry(self.frame_range, width=8)
        self.entry_leftlon.grid(row=0, column=1, padx=5, pady=5)

        self.label_leftlat = tk.Label(self.frame_range, text='左上角纬度:')
        self.label_leftlat.grid(row=0, column=2, padx=5, pady=5)
        self.entry_leftlat = tk.Entry(self.frame_range, width=8)
        self.entry_leftlat.grid(row=0, column=3, padx=5, pady=5)

        self.label_rightlon = tk.Label(self.frame_range, text='右下角经度:')
        self.label_rightlon.grid(row=1, column=0, padx=5, pady=5)
        self.entry_rightlon = tk.Entry(self.frame_range, width=8)
        self.entry_rightlon.grid(row=1, column=1, padx=5, pady=5)

        self.label_rightlat = tk.Label(self.frame_range, text='右下角纬度:')
        self.label_rightlat.grid(row=1, column=2, padx=5, pady=5)
        self.entry_rightlat = tk.Entry(self.frame_range, width=8)
        self.entry_rightlat.grid(row=1, column=3, padx=5, pady=5)

        for e in [self.entry_leftlon, self.entry_leftlat, self.entry_rightlon, self.entry_rightlat]:
            e.bind('<FocusOut>', self.__event_range_input)
            e.bind('<Return>', self.__event_range_input)
            e.bind('<Leave>', self.__event_range_input)

        self.button_send = tk.Button(self.frame_range, width=7, text='发送', command=self.__callback_send_require)
        self.button_send.grid(row=2, column=1, columnspan=2, padx=5, pady=20)

    def __callback_optionchange(self, option):

        if option == '路程与破冰':
            self.sc.grid()
            self.sct.grid()
            self.b10.grid()
            self.b11.grid()
        else:
            self.sc.grid_remove()
            self.sct.grid_remove()
            self.b10.grid_remove()
            self.b11.grid_remove()

    def __callback_adjust_point(self):
        if self.pointFrame != None:
            return

        if self.tag_temp_point != None:
            self.modis_canvas.delete(self.tag_temp_point)
            self.tag_temp_point = None

        if self.cost_tag_temp_point != None:
            self.cost_canvas.delete(self.cost_tag_temp_point)
            self.cost_tag_temp_point = None

        if self.trace_tag_temp_point != None:
            self.trace_canvas.delete(self.trace_tag_temp_point)
            self.trace_tag_temp_point = None

        self.pointFrame = tk.Toplevel()
        self.pointFrame.geometry("300x420")
        self.pointFrame.wm_attributes('-topmost',1)
        self.pointFrame.transient(root)
        self.pointFrame.resizable(width=False, height=False)
        self.pointFrame.title('Operation Points')

        self.frame_title = tk.Frame(self.pointFrame, width=300, height=50)
        self.frame_input = tk.Frame(self.pointFrame, width=300, height=70)
        self.frame_list = tk.Frame(self.pointFrame, width=300, height=200)
        self.frame_info = tk.Frame(self.pointFrame, width=300, height=100)
        self.frame_title.pack()
        self.frame_input.pack()
        self.frame_list.pack()
        self.frame_info.pack()

        self.label_info = tk.Label(self.frame_title, text='作业点坐标：', font=("黑体", 11))
        self.label_info.grid(row=1, padx=5, pady=15)

        self.label_ext = tk.Label(self.frame_title, text='（西经为-，东经为+，南纬为-，北纬为+）')
        self.label_ext.grid(row=2)

        self.label_lon = tk.Label(self.frame_input, text='经度:')
        self.label_lon.grid(row=2, column=0, padx=5, pady=15)
        self.entry_lon = tk.Entry(self.frame_input, width=8)
        self.entry_lon.grid(row=2, column=1, padx=5, pady=15)

        self.label_lat = tk.Label(self.frame_input, text='纬度:')
        self.label_lat.grid(row=2, column=2, padx=5, pady=15)
        self.entry_lat = tk.Entry(self.frame_input, width=8)
        self.entry_lat.grid(row=2, column=3, padx=5, pady=15)

        self.entry_lon.bind('<Tab>', self.__point_frame_input_check)
        self.entry_lon.bind('<FocusOut>', self.__point_frame_input_check)
        self.entry_lon.bind('<Return>', self.__point_frame_input_check)
        self.entry_lon.bind('<Leave>', self.__point_frame_input_check)

        self.entry_lat.bind('<Tab>', self.__point_frame_input_check)
        self.entry_lat.bind('<FocusOut>', self.__point_frame_input_check)
        self.entry_lat.bind('<Leave>', self.__point_frame_input_check)

        scrollbar = tk.Scrollbar(self.frame_list)
        scrollbar.grid(row=0, column=1, sticky='ns')

        var = tk.StringVar()
        self.list = tk.Listbox(self.frame_list, width=25, listvariable=var, yscrollcommand=scrollbar.set)
        self.list.grid(row=0, column=0, pady=10)
        for i in xrange(len(self.recent_op_points)):
            v = "经度"+'{:.2f}'.format(self.recent_op_points[i][0])+"，纬度"+'{:.2f}'.format(self.recent_op_points[i][1])
            self.list.insert(tk.END, v)
        # self.list.bind("<Double-Button-1>", self.__event_operation_point)
        self.list.bind('<Motion>', self.__event_listbox_motion)
        self.list.bind("<Button-1>", self.__event_operation_point)

        scrollbar.config(command=self.list.yview)

        self.label_list = tk.Label(self.frame_info, text='最近增加作业点')
        self.label_list.grid(row=1, column=1, columnspan=2)

        self.button_up = tk.Button(self.frame_info, text='↑', command=self.__shift_up_points)
        self.button_up.grid(row=2, column=0, padx=10)

        self.button_con = tk.Button(self.frame_info, text='增加', width=7, command=self.__add_operation_points)
        self.button_con.grid(row=2, column=1, padx=10, pady=10)

        self.button_con = tk.Button(self.frame_info, text='删除', width=7, command=self.__delete_operation_points)
        self.button_con.grid(row=2, column=2, padx=10, pady=10)

        self.button_down = tk.Button(self.frame_info, text='↓', command=self.__shift_down_points)
        self.button_down.grid(row=2, column=3, padx=10)

        self.pointFrame.protocol("WM_DELETE_WINDOW", self.__close_point_frame)

        return

    def __add_operation_points(self):
        lon = self.__check_input(self.entry_lon.get(),True)
        lat = self.__check_input(self.entry_lat.get(),False)

        if (lon, lat) in self.current_op_points:
            return

        try:
            i, j = self.__find_geocoordinates(lon, lat)
        except RuntimeError:
            return
        except IndexError:
            return

        self.current_op_points.append((lon, lat))

        if (lon, lat) not in self.recent_op_points:
            self.recent_op_points.append((lon, lat))
            v = "经度"+'{:.2f}'.format(lon)+"，纬度"+'{:.2f}'.format(lat)
            self.list.insert(tk.END, v)

        # draw operation point
        self.modis_canvas.delete(self.tag_temp_point)
        self.tag_temp_point = None
        if self.cost_tag_temp_point != None:
            self.cost_canvas.delete(self.cost_tag_temp_point)
            self.cost_tag_temp_point = None
        if self.trace_tag_temp_point != None:
            self.trace_canvas.delete(self.trace_tag_temp_point)
            self.trace_tag_temp_point = None

        x, y = self.__matrixcoor2canvascoor(i, j)
        self.tag_operation_point.append(self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='yellow'))
        if self.img_num == 0:
            self.cost_tag_operation_point.append(self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='yellow'))

        i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
        x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)
        self.trace_tag_operation_point.append(self.trace_canvas.create_oval(x_trace-5, y_trace-5, x_trace+5, y_trace+5, fill='yellow'))

        self.__auto_scrollbar_move()

    def __delete_operation_points(self):
        lon = float(self.entry_lon.get())
        lat = float(self.entry_lat.get())

        if (lon, lat) in self.current_op_points:
            # index = self.current_op_points.index((lon, lat))
            self.current_op_points.remove((lon, lat))
            # self.canvas.delete(self.tag_operation_point[index])

        self.__draw_operation_point()

        # print self.recent_op_points
        index = self.recent_op_points.index((lon, lat))
        self.modis_canvas.delete(self.tag_temp_point)
        self.tag_temp_point = None
        if self.cost_tag_temp_point != None:
            self.cost_canvas.delete(self.cost_tag_temp_point)
            self.cost_tag_temp_point = None
        if self.trace_tag_temp_point != None:
            self.trace_canvas.delete(self.trace_tag_temp_point)
            self.trace_tag_temp_point = None

        self.recent_op_points.remove((lon, lat))
        self.list.delete(index)

        self.entry_lon.delete('0', 'end')
        self.entry_lat.delete('0', 'end')

        self.__callback_bhp_hidepath()

    def __shift_up_points(self):
        lon = self.__check_input(self.entry_lon.get(),True)
        lat = self.__check_input(self.entry_lat.get(),False)

        index = self.recent_op_points.index((lon, lat))
        if index == 0:
            return
        else:
            self.recent_op_points[index-1], self.recent_op_points[index] = \
                self.recent_op_points[index], self.recent_op_points[index-1]
            self.list.delete(index)
            v = "经度"+'{:.2f}'.format(lon)+"，纬度"+'{:.2f}'.format(lat)
            self.list.insert(index-1, v)
            if (lon, lat) in self.current_op_points and \
                    (self.recent_op_points[index-1][0], self.recent_op_points[index-1][1] in self.current_op_points):
                index_c = self.current_op_points.index((lon, lat))
                self.current_op_points[index_c-1], self.current_op_points[index_c] = \
                    self.current_op_points[index_c], self.current_op_points[index_c-1]

    def __shift_down_points(self):
        lon = self.__check_input(self.entry_lon.get(),True)
        lat = self.__check_input(self.entry_lat.get(),False)

        index = self.recent_op_points.index((lon, lat))
        if index == len(self.recent_op_points)-1:
            return
        else:
            self.recent_op_points[index+1], self.recent_op_points[index] = \
                self.recent_op_points[index], self.recent_op_points[index+1]
            self.list.delete(index)
            v = "经度"+'{:.2f}'.format(lon)+"，纬度"+'{:.2f}'.format(lat)
            self.list.insert(index+1, v)
            if (lon, lat) in self.current_op_points and \
                    (self.recent_op_points[index+1][0], self.recent_op_points[index+1][1] in self.current_op_points):
                index_c = self.current_op_points.index((lon, lat))
                self.current_op_points[index_c+1], self.current_op_points[index_c] = \
                    self.current_op_points[index_c], self.current_op_points[index_c+1]

    def __callback_send_require(self):
        if self.entry_mail.get()=='' or self.entry_leftlon.get()=='' or self.entry_leftlat.get()=='' \
                or self.entry_rightlon.get()=='' or self.entry_rightlat.get()=='':
            tkMessageBox.showerror('Error', '输入不完整')

        self.modis_canvas.delete(self.tag_left_point[0])
        self.modis_canvas.delete(self.tag_right_point[0])
        self.cost_canvas.delete(self.tag_left_point[1])
        self.cost_canvas.delete(self.tag_right_point[1])

        leftlon = self.__check_input(self.entry_leftlon.get(), True)
        leftlat = self.__check_input(self.entry_leftlat.get(), False)

        rightlon = self.__check_input(self.entry_rightlon.get(), True)
        rightlat = self.__check_input(self.entry_rightlat.get(), False)

        pos_text1 = "(" + str(abs(leftlat))
        if leftlat > 0:
            pos_text1 = pos_text1 + "N " + str(abs(leftlon))
        else:
            pos_text1 = pos_text1 + "S " + str(abs(leftlon))
        if leftlon > 0:
            pos_text1 = pos_text1 + "E)"
        else:
            pos_text1 = pos_text1 + "W)"

        pos_text2 = "(" + str(abs(rightlat))
        if rightlat > 0:
            pos_text2 = pos_text2 + "N " + str(abs(rightlon))
        else:
            pos_text2 = pos_text2 + "S " + str(abs(rightlon))
        if rightlon > 0:
            pos_text2 = pos_text2 + "E)"
        else:
            pos_text2 = pos_text2 + "W)"

        text = '请求SAR图，所需要覆盖面积为' + pos_text1 + '到' + pos_text2

        sent = send_mail.send(self.entry_mail.get(), text)
        if sent:
            tkMessageBox.showinfo('Info', '邮件发送成功')
        else:
            tkMessageBox.showerror('Error', '邮件发送失败')
        self.sarFrame.destroy()

    def __close_point_frame(self):
        self.pointFrame.destroy()
        self.pointFrame = None

    # event callbacks
    def __event_canvas_click(self, event):

        canvas = event.widget
        x, y = int(canvas.canvasx(event.x)), int(canvas.canvasy(event.y))     # x y is canvas coordinates

        if x <= 0 or x >= self.modis_imtk.width() or y <= 0 or y >= self.modis_imtk.height():
            return

        status = self.mouse_status.get()

        if status == 0:     # normal
            canvas.scan_mark(event.x, event.y)

        elif status == 1:   # click to set starting point
            i, j = self.__canvascoor2matrixcoor(x, y)
            lon = self.lonlat_mat[i, j][0]
            lat = self.lonlat_mat[i, j][1]

            self.e1.delete(0, 'end')
            self.e1.insert(0, str('%0.2f'%lon))
            self.e2.delete(0, 'end')
            self.e2.insert(0, str('%0.2f'%lat))

            self.__draw_start_point()

        elif status == 2:   # click to set ending point
            i, j = self.__canvascoor2matrixcoor(x, y)
            lon = self.lonlat_mat[i, j][0]
            lat = self.lonlat_mat[i, j][1]

            self.e3.delete(0, 'end')
            self.e3.insert(0, str('%0.2f'%lon))
            self.e4.delete(0, 'end')
            self.e4.insert(0, str('%0.2f'%lat))

            self.__draw_end_point()

        elif status == 3:   # click to add working point
            i, j = self.__canvascoor2matrixcoor(x, y)
            lon = round(self.lonlat_mat[i, j][0], 2)
            lat = round(self.lonlat_mat[i, j][1], 2)

            self.current_op_points.append((lon, lat))

            if (lon, lat) not in self.recent_op_points:
                self.recent_op_points.append((lon, lat))

            # draw operation point
            self.modis_canvas.delete(self.tag_temp_point)
            self.tag_temp_point = None
            if self.cost_tag_temp_point != None:
                self.cost_canvas.delete(self.cost_tag_temp_point)
                self.cost_tag_temp_point = None
            if self.trace_tag_temp_point != None:
                self.trace_canvas.delete(self.trace_tag_temp_point)
                self.trace_tag_temp_point = None

            self.tag_operation_point.append(self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='yellow'))
            if self.img_num == 0:
                self.cost_tag_operation_point.append(self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='yellow'))

            i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
            x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)
            self.trace_tag_operation_point.append(self.trace_canvas.create_oval(x_trace-5, y_trace-5, x_trace+5, y_trace+5, fill='yellow'))

            self.mouse_status.set(0)

            self.__auto_scrollbar_move()

        else:
            raise Exception('mouse status error')

    def __event_canvas_move(self, event):

        canvas = event.widget

        if self.mouse_status.get() == 0:     # normal
            canvas.scan_dragto(event.x, event.y, gain=1)
            if self.img_num == 0:
                self.cost_canvas.scan_dragto(event.x-690, event.y-690, gain=1)

    def __event_canvas_motion(self, event):
        canvas = event.widget

        x, y = int(canvas.canvasx(event.x)), int(canvas.canvasy(event.y))     # x y is canvas coordinates

        if x <= 0 or x >= self.modis_imtk.width() or y <= 0 or y >= self.modis_imtk.height():
            return

        i, j = self.__canvascoor2matrixcoor(x, y)

        lon = self.lonlat_mat[i, j][0]
        lat = self.lonlat_mat[i, j][1]
        prob = self.prob_mat[i, j]
        mask = self.ice_mat[i, j]

        areatext = '估计浮冰面积<'
        if prob[2] > 0.3:
            areatext = areatext + '{:.2f}'.format(prob[2]*25) + 'km2'
        else:
            areatext = areatext + '{:.2f}'.format(prob[1]*25) + 'km2'

        text_cotent = '海的概率: %.4f'%prob[0] + '\n' + '薄冰/云的概率: %.4f'%prob[1] + '\n' + '厚冰/云的概率: %.4f'%prob[2]

        if mask:
            text_cotent = text_cotent + '(厚冰)'
        else:
            text_cotent = text_cotent + '(厚云)'

        text_cotent = text_cotent + '\n' + areatext

        postion = ''
        if lat > 0:
            postion = postion + '%.2f °N'%abs(lat)
        else:
            postion = postion + '%.2f °S'%abs(lat)

        if lon > 0:
            postion = postion + ', %.2f °E'%abs(lon)
        else:
            postion = postion + ', %.2f °W'%abs(lon)

        text_cotent = '\n\n' + '经纬度：' + postion + '\n' + text_cotent + '\n\n'

        self.message_var.set(text_cotent)

    def __event_trace_press(self, event):
        self.trace_canvas.scan_mark(event.x, event.y)

    def __event_trace_move(self, event):
        # print(event.x, event.y)
        self.trace_canvas.scan_dragto(event.x, event.y, gain=1)

    def __event_entry_input(self, event):

        entry = event.widget

        gstart = [self.e1, self.e2]     #g means group
        gend = [self.e3, self.e4]

        g = gstart if entry in gstart else gend

        if g[0].get() == "" and g[1].get() == "":
            return

        try:
            lon = -1
            lat = -1
            if g[0].get() != "":
                lon = self.__check_input(g[0].get(), True)
            if g[1].get() != "":
                lat = self.__check_input(g[1].get(), False)
            if g[0].get() != "" and g[1].get() != "":
                i, j = self.__find_geocoordinates(lon, lat)

        except ValueError:
            if entry.get() != "":
                entry['bg'] = 'red'
            self.is_gen_path = False

        except IndexError:
            if entry.get() != "":
                entry['bg'] = 'blue'
            self.is_gen_path = False

        except RuntimeError:
            g[0]['bg'] = 'yellow'
            g[1]['bg'] = 'yellow'
            self.is_gen_path = False

        else:
            entry['bg'] = 'white'
            if g[0]['bg'] == 'yellow' or g[1]['bg'] == 'yellow':
                g[0]['bg'] = 'white'
                g[1]['bg'] = 'white'
            self.is_gen_path = True

        # draw anyway even if exception
        if g == gstart:
            self.__draw_start_point()
        else:
            self.__draw_end_point()

    def __event_listbox_motion(self, event):
        try:
            items = self.list.curselection()
            index = items[0]

            if index < len(self.recent_op_points):
                lon, lat = self.recent_op_points[index]
                self.entry_lon.delete(0, 'end')
                self.entry_lon.insert(0, str('%0.2f'%lon))
                self.entry_lat.delete(0, 'end')
                self.entry_lat.insert(0, str('%0.2f'%lat))
                self.__draw_temp_point()
        except:
            pass

    def __event_operation_point(self, event):
        try:
            items = self.list.curselection()
            index = items[0]

            if index < len(self.recent_op_points):
                lon, lat = self.recent_op_points[index]
                self.entry_lon.delete(0, 'end')
                self.entry_lon.insert(0, str('%0.2f'%lon))
                self.entry_lat.delete(0, 'end')
                self.entry_lat.insert(0, str('%0.2f'%lat))
                self.__draw_temp_point()
        except:
            pass

    def __point_frame_input_check(self, event):
        entry = event.widget

        if self.entry_lon.get() == "" and self.entry_lat.get() == "":
            return

        try:
            lon = -1
            lat = -1
            if self.entry_lon.get() != "":
                lon = self.__check_input(self.entry_lon.get(), True)
            if self.entry_lat.get() != "":
                lat = self.__check_input(self.entry_lat.get(), False)
            if self.entry_lat.get() != "" and self.entry_lon.get() != "":
                i, j = self.__find_geocoordinates(lon, lat)

        except ValueError:
            if entry.get() != '':
                entry['bg'] = 'red'
            self.is_add_op = False

        except IndexError:
            if entry.get() != '':
                entry['bg'] = 'blue'
            self.is_add_op = False

        except RuntimeError:
            self.entry_lon['bg'] = 'yellow'
            self.entry_lat['bg'] = 'yellow'
            self.is_add_op = False

        else:
            entry['bg'] = 'white'
            if self.entry_lon['bg'] == 'yellow' or self.entry_lat['bg'] == 'yellow':
                self.entry_lon['bg'] = 'white'
                self.entry_lat['bg'] = 'white'
            self.is_add_op = True

        self.__draw_temp_point()

    def __event_email_check(self, event):
        pattern = '^(\w)+(\.\w+)*@(\w)+((\.\w+)+)$'
        if self.entry_mail.get() == '':
            return
        if re.match(pattern, self.entry_mail.get()) == None:
            self.entry_mail['bg'] = 'red'
            self.is_send_sar = False
        else:
            self.entry_mail['bg'] = 'white'
            self.is_send_sar = True

    def __event_range_input(self, event):
        entry = event.widget

        gleft = [self.entry_leftlon, self.entry_leftlat]     #g means group
        gright = [self.entry_rightlon, self.entry_rightlat]

        g = gleft if entry in gleft else gright

        if g[0].get() == "" and g[1].get() == "":
            return

        try:
            lon = -1
            lat = -1
            if g[0].get() != "":
                lon = self.__check_input(g[0].get(), True)
            if g[1].get() != "":
                lat = self.__check_input(g[1].get(), False)
            if g[0].get() != "" and g[1].get() != "":
                i, j = self.__find_geocoordinates(lon, lat)

        except ValueError:
            if entry.get() != "":
                entry['bg'] = 'red'
            self.is_send_sar = False

        except IndexError:
            if entry.get() != "":
                entry['bg'] = 'blue'
            self.is_send_sar = False

        except RuntimeError:
            g[0]['bg'] = 'yellow'
            g[1]['bg'] = 'yellow'
            self.is_send_sar = False

        else:
            entry['bg'] = 'white'
            if g[0]['bg'] == 'yellow' or g[1]['bg'] == 'yellow':
                g[0]['bg'] = 'white'
                g[1]['bg'] = 'white'
            self.is_send_sar = True

        # draw anyway even if exception
        if g == gleft:
            self.__draw_left_point()
        else:
            self.__draw_right_point()

    # draw functions
    def __draw_start_point(self):

        if self.tag_start_point != None:
            self.modis_canvas.delete(self.tag_start_point)
            self.tag_start_point = None

        if self.cost_tag_start_point != None:
            self.cost_canvas.delete(self.cost_tag_start_point)
            self.cost_tag_start_point = None

        if self.trace_tag_start_point != None:
            self.trace_canvas.delete(self.trace_tag_start_point)
            self.trace_tag_start_point = None

        if self.e1.get() == '' or self.e2.get() == '':  #todo
            return

        lon = self.__check_input(self.e1.get(), True)
        lat = self.__check_input(self.e2.get(), False)

        i, j = self.__find_geocoordinates(lon, lat)
        x, y = self.__matrixcoor2canvascoor(i, j)

        self.tag_start_point = self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='red')
        if self.img_num == 0:
            self.cost_tag_start_point = self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='red')

        i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
        x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)

        self.trace_tag_start_point = self.trace_canvas.create_oval(x_trace-5, y_trace-5, x_trace+5, y_trace+5, fill='red')

    def __draw_end_point(self):

        if self.tag_end_point != None:
            self.modis_canvas.delete(self.tag_end_point)
            self.tag_end_point = None

        if self.cost_tag_end_point != None:
            self.cost_canvas.delete(self.cost_tag_end_point)
            self.cost_tag_end_point = None

        if self.trace_tag_end_point != None:
            self.trace_canvas.delete(self.trace_tag_end_point)
            self.trace_tag_end_point = None

        if self.e3.get() == '' or self.e4.get() == '':  #todo
            return

        lon = self.__check_input(self.e3.get(), True)
        lat = self.__check_input(self.e4.get(), False)

        i, j = self.__find_geocoordinates(lon, lat)
        x, y = self.__matrixcoor2canvascoor(i, j)

        self.tag_end_point = self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='blue')
        if self.img_num == 0:
            self.cost_tag_end_point = self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='blue')

        i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
        x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)

        self.trace_tag_end_point = self.trace_canvas.create_oval(x_trace-5, y_trace-5, x_trace+5, y_trace+5, fill='blue')

    def __draw_temp_point(self):
        if self.tag_temp_point != None:
            self.modis_canvas.delete(self.tag_temp_point)
            self.tag_temp_point = None

        if self.cost_tag_temp_point != None:
            self.cost_canvas.delete(self.cost_tag_temp_point)
            self.cost_tag_temp_point = None

        if self.trace_tag_temp_point != None:
            self.trace_canvas.delete(self.trace_tag_temp_point)
            self.trace_tag_temp_point = None

        try:
            if self.entry_lon.get() == '' or self.entry_lat.get() == '':  #todo
                return

            lon = self.__check_input(self.entry_lon.get(), True)
            lat = self.__check_input(self.entry_lat.get(), False)

            i, j = self.__find_geocoordinates(lon, lat)
            x, y = self.__matrixcoor2canvascoor(i, j)

            self.tag_temp_point = self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='green')
            if self.img_num == 0:
                self.cost_tag_temp_point = self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='green')

            i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
            x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)

            self.trace_tag_temp_point = self.trace_canvas.create_oval(x_trace-5, y_trace-5, x_trace+5, y_trace+5, fill='green')
        except:
            return

    def __draw_operation_point(self):
        if self.tag_operation_point != []:
            for i in xrange(0, len(self.tag_operation_point)):
                self.modis_canvas.delete(self.tag_operation_point[i])
            self.tag_operation_point = []

        if self.cost_tag_operation_point != []:
            for i in xrange(0, len(self.cost_tag_operation_point)):
                self.cost_canvas.delete(self.cost_tag_operation_point[i])
            self.cost_tag_operation_point = []

        if self.trace_tag_operation_point != []:
            for i in xrange(0, len(self.trace_tag_operation_point)):
                self.trace_canvas.delete(self.trace_tag_operation_point[i])
            self.trace_tag_operation_point = []

        for item in self.current_op_points:
            lon, lat = item

            i, j = self.__find_geocoordinates(lon, lat)
            x, y = self.__matrixcoor2canvascoor(i, j)

            self.tag_operation_point.append(self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='yellow'))
            if self.img_num == 0:
                self.cost_tag_operation_point.append(self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='yellow'))

            i_trace, j_trace = self.__lonlat2matrixcoor_trace(lon, lat)
            x_trace, y_trace = self.__matrixcoor2canvascoor_trace(i_trace, j_trace)
            self.trace_tag_operation_point.append(self.trace_canvas.create_oval(x_trace-5, y_trace-5, x_trace+5, y_trace+5, fill='yellow'))

    def __draw_left_point(self):
        if self.tag_left_point != None:
            self.modis_canvas.delete(self.tag_left_point)
            self.tag_left_point = None

        if self.cost_tag_left_point != None:
            self.cost_canvas.delete(self.cost_tag_left_point)
            self.cost_tag_left_point = None

        if self.entry_leftlon.get() == '' or self.entry_leftlat.get() == '':  #todo
            return

        lon = self.__check_input(self.entry_leftlon.get(), True)
        lat = self.__check_input(self.entry_leftlat.get(), False)

        i, j = self.__find_geocoordinates(lon, lat)
        x, y = self.__matrixcoor2canvascoor(i, j)

        self.tag_left_point = self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='purple')
        if self.img_num == 0:
            self.cost_tag_left_point = self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='purple')

    def __draw_right_point(self):

        if self.tag_right_point != None:
            self.modis_canvas.delete(self.tag_right_point)
            self.tag_right_point = None

        if self.cost_tag_right_point != None:
            self.cost_canvas.delete(self.cost_tag_right_point)
            self.cost_tag_right_point = None

        if self.entry_rightlon.get() == '' or self.entry_rightlat.get() == '':  #todo
            return

        lon = self.__check_input(self.entry_rightlon.get(), True)
        lat = self.__check_input(self.entry_rightlat.get(), False)

        i, j = self.__find_geocoordinates(lon, lat)
        x, y = self.__matrixcoor2canvascoor(i, j)

        self.tag_right_point = self.modis_canvas.create_oval(x-5, y-5, x+5, y+5, fill='purple')
        if self.img_num == 0:
            self.cost_tag_right_point = self.cost_canvas.create_oval(x-5, y-5, x+5, y+5, fill='purple')

    def __draw_path(self):

        if self.tag_path != []:
            for i in xrange(0, len(self.tag_path)):
                self.modis_canvas.delete(self.tag_path[i])
            self.tag_path = []

        if self.cost_tag_path != []:
            for i in xrange(0, len(self.cost_tag_path)):
                self.cost_canvas.delete(self.cost_tag_path[i])
            self.cost_tag_path = []

        if self.trace_tag_path != []:
            for i in xrange(0, len(self.trace_tag_path)):
                self.trace_canvas.delete(self.trace_tag_path[i])
            self.trace_tag_path = []

        if self.path == []:
            return

        width = 6
        if self.zoom_factor <= 0.8:
            width = 4
        if self.zoom_factor <= 0.2:
            width = 2
        width_trace = 5

        for i in range(0, len(self.path)-1):
            cx, cy = self.__matrixcoor2canvascoor(self.path[i][0], self.path[i][1])
            nx, ny = self.__matrixcoor2canvascoor(self.path[i+1][0], self.path[i+1][1])
            self.tag_path.append(self.modis_canvas.create_line(cx, cy, nx, ny, fill='#7FFF00', width=width))
            if self.img_num == 0:
                self.cost_tag_path.append(self.cost_canvas.create_line(cx, cy, nx, ny, fill='#7FFF00', width=width))

            [clon_trace, clat_trace] = self.lonlat_mat[self.path[i][0], self.path[i][1]]
            # print clon_trace, clat_trace
            ci_trace, cj_trace = self.__lonlat2matrixcoor_trace(clon_trace, clat_trace)
            cx_trace, cy_trace = self.__matrixcoor2canvascoor_trace(ci_trace, cj_trace)
            [nlon_trace, nlat_trace] = self.lonlat_mat[self.path[i+1][0], self.path[i+1][1]]
            ni_trace, nj_trace = self.__lonlat2matrixcoor_trace(nlon_trace, nlat_trace)
            nx_trace, ny_trace = self.__matrixcoor2canvascoor_trace(ni_trace, nj_trace)
            self.trace_tag_path.append(self.trace_canvas.create_line(cx_trace, cy_trace, nx_trace, ny_trace, fill='#7FFF00', width=width_trace))

    def __draw_graticule(self):

        # According to new data, the modis image is transformed by zenithal projection.
        # We can assume that longitude is straight line, latitude is circle (this is assured by zenithal projection)
        # and the polar point should be seated in the image (this is not)
        # Otherwise, we can use code in old system to draw graticule which can deal with twisted graticule

        # This function cannot deal with situation that polar is not within the image
        # Todo :
        #   1. To improve accuracy, use canvas coordinates directly (like drawing latitude) to draw longitude
        #   2. Deal with sitution that polar is not within the image

        for i in xrange(0, len(self.tag_graticule)):
            self.modis_canvas.delete(self.tag_graticule[i])
        self.tag_graticule = []

        if self.cost_tag_graticule != []:
            for i in xrange(0, len(self.cost_tag_graticule)):
                self.cost_canvas.delete(self.cost_tag_graticule[i])
            self.cost_tag_graticule = []

        lon_mat = self.lonlat_mat[:, :, 0]
        lat_mat = self.lonlat_mat[:, :, 1]
        ilen, jlen = lat_mat.shape

        polar = [None, None]  # lat_mat[polar] is 90N or 90S

        width = 2
        fontsize = 11
        if self.zoom_factor <= 0.6:
            width = 1
            fontsize = 10
        if self.zoom_factor <= 0.2:
            width = 1
            fontsize = 9

        # find vertical longitude line 180 or 0
        j_list = []
        for i in range(0, ilen, 10):
            for v in [0, 180]:
                j = int(np.fabs(lon_mat[i, :] - v).argmin())
                diff = np.fabs(lon_mat[i, j] - v)
                if diff < 0.5:
                    j_list.append(int(j))

        if j_list != []: # founded
            target_j = Counter(j_list).most_common(1)[0][0] # mode of j_list
            x1, y1 = self.__matrixcoor2canvascoor(0, target_j)
            x2, y2 = self.__matrixcoor2canvascoor(ilen-1, target_j)
            g1 = self.modis_canvas.create_line(x1, y1, x2, y2, fill='SeaGreen', width=width)
            t1 = self.modis_canvas.create_text(x2-2, y2-1, anchor='se', font=("Purisa",fontsize), fill='SeaGreen', text=str(int(round(lon_mat[ilen-1, target_j]))))
            self.tag_graticule.append(g1)
            self.tag_graticule.append(t1)
            if self.img_num == 0:
                g2 = self.cost_canvas.create_line(x1, y1, x2, y2, fill='SeaGreen', width=width)
                t2 = self.cost_canvas.create_text(x2-2, y2-1, anchor='se', font=("Purisa",fontsize), fill='SeaGreen', text=str(int(round(lon_mat[ilen-1, target_j]))))
                self.cost_tag_graticule.append(g2)
                self.cost_tag_graticule.append(t2)

            polar[1] = int(target_j)

        # draw other longitude lines, such as 150(-30), 120(-60) etc
        interv = 3
        for v in range(0+interv, 180, interv):

            self.modis_canvas.update_idletasks()
            self.cost_canvas.update_idletasks()

            # draw line v(-180+v)
            # search by column, for every column j find i that lon[i, j] == v (or -180+v)
            # draw a line between (i0, j0) and (in, jn)
            # notice that vertical line cannot be drawn by this way

            i_list, j_list = [], []
            for j in range(0, jlen, 2):
                for t in [v, -180+v]:
                    i = int(np.fabs(lon_mat[:, j] - t).argmin())
                    diff = np.fabs(lon_mat[i, j] - t)
                    if diff < 0.5:
                        i_list.append(i)
                        j_list.append(j)

            if i_list != []:
                x1, y1 = self.__matrixcoor2canvascoor(i_list[0], j_list[0])
                x2, y2 = self.__matrixcoor2canvascoor(i_list[-1], j_list[-1])
                g1 = self.modis_canvas.create_line(x1, y1, x2, y2, fill='SeaGreen', width=width)
                t1 = self.modis_canvas.create_text(x2-2, y2-1, anchor='se', font=("Purisa",fontsize, 'bold'), fill='SeaGreen', text=str(int(round(lon_mat[i_list[-1], j_list[-1]]))))
                self.tag_graticule.append(g1)
                self.tag_graticule.append(t1)
                if self.img_num == 0:
                    g2 = self.cost_canvas.create_line(x1, y1, x2, y2, fill='SeaGreen', width=width)
                    t2 = self.cost_canvas.create_text(x2-2, y2-1, anchor='se', font=("Purisa",fontsize, 'bold'), fill='SeaGreen', text=str(int(round(lon_mat[i_list[-1], j_list[-1]]))))
                    self.cost_tag_graticule.append(g2)
                    self.cost_tag_graticule.append(t2)

                if v == 90:
                    polar[0] = int(i_list[0])   # 90 longitude line is totally horizontal

        if polar[0] != None and polar[1] != None:
            # print polar[0], polar[1]
            assert 0 <= polar[0] < ilen
            assert 0 <= polar[1] < jlen

            # draw latitude circles
            # notice that all latitude circles center at polar
            # so once found the center and radius, then the circle can be drawn
            interv = 1
            for v in range(0, 90, interv):

                self.modis_canvas.update_idletasks()
                self.cost_canvas.update_idletasks()

                t = v if lat_mat[0, 0] > 0 else -v

                # find a point (i, j) on the circle that lat_mat[i, j] = t
                i = polar[0]
                j = int(np.fabs(lat_mat[i, :] - t).argmin())    # first, try to find (i, j) that i equals polar[0]
                if np.fabs(lat_mat[i, j] - t) > 0.5:            # if not found, try (i, j) that j equals ploar[1]
                    j = polar[1]
                    i = int(np.fabs(lat_mat[:, j] - t).argmin())
                    if np.fabs(lat_mat[i, j] - t) > 0.5:
                        continue    # also not found , no more work to draw this latitude circle

                # from now on, use canvas coordinates instead of matrix coordinates to improve accuracy
                x0, y0 = self.__matrixcoor2canvascoor(polar[0], polar[1])   # canvas coordinates of the center
                x1, y1 = self.__matrixcoor2canvascoor(i, j)                 # canvas coordinates of (i, j)
                radius = ((x1-x0)**2 + (y1-y0)**2)**0.5


                # the target latitude line is a circle
                # the center is (x0, y0), radius is known
                # by circle formula, we calculate points on the circle and draw it

                xlen, ylen = self.modis_imtk.width(), self.modis_imtk.height()

                assert self.modis_imtk.width() == self.cost_imtk.width()
                assert self.modis_imtk.height() == self.cost_imtk.height()

                for sign in [1, -1]: # lower half circle and upper half circle
                    circle_points = [[]]
                    for x in range(max(int(x0-radius), 0), min(int(x0+radius+1), xlen)):    #range function creates a left-close-right-open interval [,) , thus +1 on right side
                        y = y0 + sign * (radius**2 - (x-x0)**2)**0.5    # circle formula
                        if 0<= y < ylen:
                            circle_points[-1].append((x, y))
                        else:
                            if circle_points[-1] != []:
                                circle_points.append([])
                            else:
                                continue

                    for points in circle_points:

                        for i in range(0, len(points)-1):
                            cx, cy = points[i]
                            nx, ny = points[i+1]
                            g1 = self.modis_canvas.create_line(cx, cy, nx, ny, fill='SeaGreen', width=width)
                            self.tag_graticule.append(g1)
                            if self.img_num == 0:
                                g2 = self.cost_canvas.create_line(cx, cy, nx, ny, fill='SeaGreen', width=width)
                                self.cost_tag_graticule.append(g2)

        # Code for drawing any twisted graticule (old way) are preserved below, too.

        if polar[0] == None or polar[1] == None:
            # draw latitude lines
            for v in range(50, 90, 1):
                line_points1 = []
                line_points2 = []
                for j in range(0, jlen, 1):
                    lat = lat_mat[:, j]
                    i = int(np.fabs(lat - v).argmin())
                    diff = np.fabs(lat[i] - v)
                    if i > 0 and i < ilen-1  and diff < 0.1:
                        if lon_mat[i][j] <= 0:
                            line_points1.append((i, j, lon_mat[i][j]))
                        else:
                            line_points2.append((i,j,lon_mat[i][j]))
                line_points1=sorted(line_points1,key=lambda line_points1 : line_points1[2])
                line_points2=sorted(line_points2,key=lambda line_points2 : line_points2[2])

                for i in range(len(line_points1)-1):
                    cx, cy = self.__matrixcoor2canvascoor(line_points1[i][0], line_points1[i][1])
                    nx, ny = self.__matrixcoor2canvascoor(line_points1[i+1][0], line_points1[i+1][1])
                        # g = self.canvas.create_line(cx, cy, nx, ny, fill='yellow', width=1.5)
                    g1 = self.modis_canvas.create_line(cx, cy, nx, ny, fill='SeaGreen', width=width)
                    self.tag_graticule.append(g1)
                    if self.img_num == 0:
                        g2 = self.cost_canvas.create_line(cx, cy, nx, ny, fill='SeaGreen', width=width)
                        self.cost_tag_graticule.append(g2)
                    if i == len(line_points1) - 2:
                        t1 = self.modis_canvas.create_text(nx-2, ny-1, anchor='se', font=("Purisa",fontsize,'bold'), fill='SeaGreen',
                                                    text=str(int(round(lat_mat[line_points1[i+1][0], line_points1[i+1][1]]))))
                        self.tag_graticule.append(t1)
                        if self.img_num == 0:
                            t2 = self.cost_canvas.create_text(nx-2, ny-1, anchor='se', font=("Purisa",fontsize,'bold'), fill='SeaGreen',
                                                    text=str(int(round(lat_mat[line_points1[i+1][0], line_points1[i+1][1]]))))
                            self.cost_tag_graticule.append(t2)
                for i in range(len(line_points2)-1):
                    cx, cy = self.__matrixcoor2canvascoor(line_points2[i][0], line_points2[i][1])
                    nx, ny = self.__matrixcoor2canvascoor(line_points2[i+1][0], line_points2[i+1][1])
                        # g = self.canvas.create_line(cx, cy, nx, ny, fill='yellow', width=1.5)
                    g1 = self.modis_canvas.create_line(cx, cy, nx, ny, fill='SeaGreen', width=width)
                    self.tag_graticule.append(g1)
                    if self.img_num == 0:
                        g2 = self.cost_canvas.create_line(cx, cy, nx, ny, fill='SeaGreen', width=width)
                        self.cost_tag_graticule.append(g2)
                    if i == len(line_points2) - 2:
                        t1 = self.modis_canvas.create_text(nx-2, ny-1, anchor='se', font=("Purisa",fontsize,'bold'), fill='SeaGreen',
                                                    text=str(int(round(lat_mat[line_points2[i+1][0], line_points2[i+1][1]]))))
                        self.tag_graticule.append(t1)
                        if self.img_num == 0:
                            t2 = self.cost_canvas.create_text(nx-2, ny-1, anchor='se', font=("Purisa",fontsize,'bold'), fill='SeaGreen',
                                                    text=str(int(round(lat_mat[line_points2[i+1][0], line_points2[i+1][1]]))))
                            self.cost_tag_graticule.append(t2)

    def __find_geocoordinates(self, longitude, latitude):

        assert isinstance(longitude, float)
        assert isinstance(latitude, float)

        lon_mat = self.lonlat_mat[:, :, 0]
        lat_mat = self.lonlat_mat[:, :, 1]
        ilen, jlen = lat_mat.shape

        vset = set([])
        for i in range(1, ilen-1):      # for each row i, find all j that (lon_mat[i, j] - lon) <= 0.2
            for j in (np.fabs(lon_mat[i, :] - longitude) < 0.2).nonzero()[0].tolist():
                vset.add((i, int(j)))


        if len(vset) == 0:
            # not found, raise error
            print 'longitude not found, target lon %s, lat %s'%(longitude, latitude)
            raise RuntimeError('longitude not found, vset 0')

        vlist = list(vset)
        lat = np.array([lat_mat[v[0], v[1]] for v in vlist])
        t = np.fabs(lat - latitude).argmin()
        diff =  np.fabs(lat[t] - latitude)

        if diff > 0.5:          # so that precision of lon is 0.2, but precision of lat is 0.5
            print 'latitude not found, target lon %s, lat %s'%(longitude, latitude)
            raise RuntimeError('latitude not found')

        i, j = vlist[t]
        return int(i), int(j)

    def __rescale(self, new_factor):

        assert new_factor in self.zoom_level

        # save scrollbar position before rescaling
        xa, xb = self.modis_canvas.xview()
        ya, yb = self.modis_canvas.yview()

        xa_c, xb_c = self.cost_canvas.xview()
        ya_c, yb_c = self.cost_canvas.yview()

        # do rescaling works
        self.zoom_factor = new_factor
        self.zoom_text.set('%d' % (new_factor * 400) + '%')

        img = self.modisimg
        img_c = self.costimg

        new_size = (int(img.size[0] * new_factor), int(img.size[1] * new_factor))
        self.modis_imtk = ImageTk.PhotoImage(img.resize(new_size))          # img is not resized
        self.modis_canvas.create_image(0, 0, image=self.modis_imtk, anchor='nw')
        self.modis_canvas.config(scrollregion=(0, 0, new_size[0], new_size[1]))

        new_size_c = (int(img_c.size[0] * new_factor), int(img_c.size[1] * new_factor))
        if self.img_num == 0:
            self.cost_imtk = ImageTk.PhotoImage(img_c.resize(new_size))          # img is not resized
            self.img_imtk = []
            self.img_imtk.append(self.cost_imtk)
            pptpath = 'ppt/'
            fs = os.listdir(pptpath)
            jpgfiles = filter(lambda s: s.endswith('JPG'), fs)
            for i in range(0, len(jpgfiles)):
                pptImage = Image.open(pptpath+jpgfiles[i])
                width, height = pptImage.size
                pptImage = pptImage.resize((width/24*17, height/24*17))
                self.img_imtk.append(ImageTk.PhotoImage(pptImage))
            self.img_canvases = self.cost_canvas.create_image(0, 0, image=self.img_imtk[self.img_num], anchor='nw')
            self.cost_canvas.config(scrollregion=(0, 0, new_size_c[0], new_size_c[1]))

        # for i in range(0, len(self.img_imtk)):
        #     print(self.img_imtk[i])

        self.__draw_start_point()
        self.__draw_end_point()
        self.__draw_path()
        self.__draw_temp_point()

        if self.tag_operation_point != []:
            self.__draw_operation_point()

        if self.tag_graticule != []:
            self.__draw_graticule()

        # fix wrong position of scrollbar after rescaling

        xm, ym = 0.0, 0.0   # x middle, y middle
        if self.path != []:
            px1, py1 = self.__matrixcoor2canvascoor(self.path[0][0], self.path[0][1])
            px2, py2 = self.__matrixcoor2canvascoor(self.path[-1][0], self.path[-1][1])
            xm = ((px1 + px2) / 2.0) / self.modis_imtk.width()
            ym = ((py1 + py2) / 2.0) / self.modis_imtk.height()

            xm_c = ((px1 + px2) / 2.0) / self.modis_imtk.width()
            ym_c = ((py1 + py2) / 2.0) / self.modis_imtk.height()
            print 'hit'
        else:
            xm = (xa + xb)/2.0
            ym = (ya + yb)/2.0
            xm_c = (xa_c + xb_c)/2.0
            ym_c = (ya_c + yb_c)/2.0

        nxlen = float(self.modis_canvas['width']) / new_size[0]       # new xbar len
        nylen = float(self.modis_canvas['height']) / new_size[1]
        nxa = (xm - nxlen/2.0)                                  # new xa
        nya = (ym - nylen/2.0)

        nxlen_c = float(self.cost_canvas['width']) / new_size_c[0]       # new xbar len
        nylen_c = float(self.cost_canvas['height']) / new_size_c[1]
        nxa_c = (xm_c - nxlen_c/2.0)                                  # new xa
        nya_c = (ym_c - nylen_c/2.0)

        self.modis_canvas.xview_moveto(nxa)
        self.modis_canvas.yview_moveto(nya)

        if self.img_num == 0:
            self.cost_canvas.xview_moveto(nxa_c)
            self.cost_canvas.yview_moveto(nya_c)

    def __rescale_trace(self, new_factor):

        assert new_factor in self.zoom_level_trace

        # save scrollbar position before rescaling
        xa, xb = self.trace_canvas.xview()
        ya, yb = self.trace_canvas.yview()

        # do rescaling works
        self.zoom_factor_trace = new_factor
        self.zoom_text_trace.set('%d' % (new_factor * 100) + '%')

        img = self.trace_image

        new_size = (int(img.size[0] * new_factor), int(img.size[1] * new_factor))
        self.trace_imtk = ImageTk.PhotoImage(img.resize(new_size))          # img is not resized
        self.trace_canvas.create_image(0, 0, image=self.trace_imtk, anchor='nw')
        self.trace_canvas.config(scrollregion=(0, 0, new_size[0], new_size[1]))

        self.__draw_start_point()
        self.__draw_end_point()
        self.__draw_path()
        self.__draw_temp_point()

        if self.trace_tag_operation_point != []:
            self.__draw_operation_point()
        # fix wrong position of scrollbar after rescaling

        xm, ym = 0.0, 0.0   # x middle, y middle
        xm = (xa + xb)/2.0
        ym = (ya + yb)/2.0

        nxlen = float(self.trace_canvas['width']) / new_size[0]       # new xbar len
        nylen = float(self.trace_canvas['height']) / new_size[1]
        nxa = (xm - nxlen/2.0)                                  # new xa
        nya = (ym - nylen/2.0)

        self.trace_canvas.xview_moveto(nxa)
        self.trace_canvas.yview_moveto(nya)

        self.__auto_scrollbar_move()

    def __auto_scrollbar_move(self):

        centeri, centerj = self.__get_new_center()

        centerx, centery = self.__matrixcoor2canvascoor(centeri, centerj)
        self.modis_canvas.xview_moveto((centerx - float(self.modis_canvas['width'])/2)/self.modis_imtk.width())
        self.modis_canvas.yview_moveto((centery - float(self.modis_canvas['height'])/2)/self.modis_imtk.height())
        if self.img_num == 0:
            self.cost_canvas.xview_moveto((centerx - float(self.cost_canvas['width'])/2)/self.cost_imtk.width())
            self.cost_canvas.yview_moveto((centery - float(self.cost_canvas['height'])/2)/self.cost_imtk.height())

        centerlon, centerlat = self.lonlat_mat[centeri, centerj, 0], self.lonlat_mat[centeri, centerj, 1]
        centeri_trace, centerj_trace = self.__lonlat2matrixcoor_trace(centerlon, centerlat)
        centerx_trace, centery_trace = self.__matrixcoor2canvascoor_trace(centeri_trace, centerj_trace)
        self.trace_canvas.xview_moveto((centerx_trace - float(self.trace_canvas['width'])/2)/self.trace_imtk.width())
        self.trace_canvas.yview_moveto((centery_trace - float(self.trace_canvas['height'])/2)/self.trace_imtk.height())

    def __get_new_center(self):

        matrixcoorlist = []
        if self.e1.get() != '' and self.e2.get() != '':
            slon = self.__check_input(self.e1.get(), True)
            slat = self.__check_input(self.e2.get(), False)
            si, sj = self.__find_geocoordinates(slon, slat)
            matrixcoorlist.append((si, sj))

        if self.e3.get() != '' and self.e4.get() != '':
            elon = self.__check_input(self.e3.get(), True)
            elat = self.__check_input(self.e4.get(), False)
            ei, ej = self.__find_geocoordinates(elon, elat)
            matrixcoorlist.append((ei, ej))

        for op_p in self.current_op_points:
            i, j = self.__find_geocoordinates(op_p[0], op_p[1])
            matrixcoorlist.append((i, j))

        if len(matrixcoorlist) == 0:
            return 0, 0
        imean = int(np.mean([coor[0] for coor in matrixcoorlist]))
        jmean = int(np.mean([coor[1] for coor in matrixcoorlist]))

        return imean, jmean

    def __lonlat2matrixcoor_trace(self, lon, lat):
        return int(np.round(8.31 * lon - 450.6)), int(np.round(471.5 * np.log(np.tan(math.pi / 4 - lat * math.pi / 360))) + 543)

    def __canvascoor2matrixcoor(self, x, y):
        assert isinstance(x, int) or isinstance(x, long)
        assert isinstance(y, int) or isinstance(y, long)
        assert 0 <= x < self.modis_imtk.width()
        assert 0 <= y < self.modis_imtk.height()

        beta = 20

        i = int((y / self.zoom_factor) / beta)  # int division
        j = int((x / self.zoom_factor) / beta)

        assert 0 <= i < self.prob_mat.shape[0]
        assert 0 <= j < self.prob_mat.shape[1]

        return i, j

    def __matrixcoor2canvascoor(self, i, j):
        assert isinstance(i, int) or isinstance(i, long)
        assert isinstance(j, int) or isinstance(j, long)
        assert 0 <= i < self.prob_mat.shape[0]
        assert 0 <= j < self.prob_mat.shape[1]

        beta = 20

        x = int(j * beta * self.zoom_factor)
        y = int(i * beta * self.zoom_factor)

        return x, y

    def __matrixcoor2canvascoor_trace(self, i, j):
        assert isinstance(i, int) or isinstance(i, long)
        assert isinstance(j, int) or isinstance(j, long)

        x = int(i * self.zoom_factor_trace)
        y = int(j * self.zoom_factor_trace)

        return x, y

    # check each entry's input
    def __check_input(self, string, is_lon):
        pattern1 = '^[+-]?\d{1,3} \d{1,2} \d{1,2} ?$'
        pattern2 = '^[+-]?\d{1,3}\.?\d*$'
        # print (re.match(pattern2, string))
        if re.match(pattern1, string) != None:          # degree, minute, second
            values = string.split(' ')
            # print values
            if float(values[1]) >= 60.00 or float(values[1]) < 0.00 or float(values[2]) >= 60.00 or float(values[2]) < 0.00:
                raise IndexError('Out of range')
            if is_lon:
                if float(values[0]) > 179.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise IndexError('Out of range')
                    if float(values[1]) > 180.00:
                        raise IndexError('Out of range')
                if float(values[0]) < -179.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise IndexError('Out of range')
                    if float(values[1]) < -180.00:
                        raise IndexError('Out of range')
            else:
                if float(values[0]) > 89.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise IndexError('Out of range')
                    if float(values[1]) > 90.00:
                        raise IndexError('Out of range')
                if float(values[0]) < -89.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise IndexError('Out of range')
                    if float(values[1]) < -90.00:
                        raise IndexError('Out of range')
            if float(values[0]) > 0:
                value = float('%.2f'%(float(values[0]) + float(values[1])/60.00 + float(values[2])/3600.00))
            else:
                value = float('%.2f'%(float(values[0]) - float(values[1])/60.00 - float(values[2])/3600.00))
        elif re.match(pattern2, string) != None:        # float
            value = float('%.2f'%float(string))
            if is_lon:
                if value > 180.00 or value < -180.00:
                    raise IndexError('Out of range')
            else:
                if value > 90.00 or value < -90.00:
                    raise IndexError('Out of range')
        else:
            raise ValueError('Illegal input')
        return value

    def __update_files(self):
        user, password = getemailpsw(3)
        user = user + '@lamda.nju.edu.cn'
        pop3_server = '210.28.132.67'
        index, t = get_email_zip.checkemail(user,password,pop3_server,0)
        if index == 0:
            tkMessageBox.showinfo('Info', '暂未有图像更新，请稍候')
            return
        unzipfile.unzipfile('download/test.zip', 'data/')
        from shutil import move
        for dirpath, dirnames, filenames in os.walk('data/test'):
            for filename in filenames:
                move('data/test/'+filename, 'data/'+filename)
                print filename
        self.__init_models()
        clearfile.clear_raster()
        try:
            # save
            ee = [self.e1, self.e2, self.e3, self.e4]
            ss = [e.get() for e in ee]

            # refresh
            self.__callback_b9_reset()

            # load
            for e, s in zip(ee, ss):
                e.insert(0, s)
            self.__draw_start_point()
            self.__draw_end_point()

            sys.stdout.flush()
        except:
            pass

def writefile():
    print 'close'
    window.operation_file = open('data/operationpoints.txt', 'w')
    for item in window.recent_op_points:
        window.operation_file.write('{:.2f}'.format(item[0])+'\t'+'{:.2f}'.format(item[1])+'\n')
    window.operation_file.close()
    root.destroy()
    os._exit(0)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Modis')
    root.resizable(width=False, height=False)

    root.overrideredirect(1)
    root.focus_set()
    root.bind("<Escape>", lambda e: e.widget.quit())

    root.protocol("WM_DELETE_WINDOW", writefile)

    window = MainWindow(root)
    root.mainloop()