# encoding:utf-8
from mtTkinter import *
import tkMessageBox
from mailutil import getemailpsw
import send_mail
class PointWindow(Frame):
    def __init__(self, master):
        self.is_send = True

        Frame.__init__(self, master)
        # self.frame_receive = Frame(master, width=500)
        self.frame_range = Frame(master, width=400)
        # self.frame_receive.pack()
        self.frame_range.pack()
        #
        # self.label_mail = Label(self.frame_receive, text='收件人邮箱：')
        # self.entry_mail = Entry(self.frame_receive, width=45)
        # self.label_mail.grid(row=0, column=0, pady=20)
        # self.entry_mail.grid(row=0, column=1, pady=20)

        # self.entry_mail.bind('<Tab>', self.__event_email_check)
        # self.entry_mail.bind('<FocusOut>', self.__event_email_check)
        # self.entry_mail.bind('<Return>', self.__event_email_check)
        self.label_blank = Label(self.frame_range, text='')
        self.label_blank.grid(row=0, column=0)

        self.label_leftlon = Label(self.frame_range, text='西界经度:')
        self.label_leftlon.grid(row=1, column=0, padx=5, pady=5)
        self.entry_leftlon = Entry(self.frame_range, width=8)
        self.entry_leftlon.grid(row=1, column=1, padx=5, pady=5)

        self.label_leftlat = Label(self.frame_range, text='北界纬度:')
        self.label_leftlat.grid(row=1, column=2, padx=5, pady=5)
        self.entry_leftlat = Entry(self.frame_range, width=8)
        self.entry_leftlat.grid(row=1, column=3, padx=5, pady=5)

        self.label_rightlon = Label(self.frame_range, text='东界经度:')
        self.label_rightlon.grid(row=2, column=0, padx=5, pady=5)
        self.entry_rightlon = Entry(self.frame_range, width=8)
        self.entry_rightlon.grid(row=2, column=1, padx=5, pady=5)

        self.label_rightlat = Label(self.frame_range, text='南界纬度:')
        self.label_rightlat.grid(row=2, column=2, padx=5, pady=5)
        self.entry_rightlat = Entry(self.frame_range, width=8)
        self.entry_rightlat.grid(row=2, column=3, padx=5, pady=5)

        self.w_long = -1
        self.e_long = -1
        self.n_lati = -1
        self.s_lati = -1

        for e in [self.entry_leftlon, self.entry_rightlon, self.entry_leftlat, self.entry_rightlat]:
            e.bind('<FocusOut>',  self.__event_range_input)
            e.bind('<Return>',  self.__event_range_input)
            e.bind('<Leave>',  self.__event_range_input)
            # e.bind('<FocusOut>', self.__check_input)
            # e.bind('<Return>', self.__check_input)

        # for e in [self.entry_leftlat, self.entry_rightlat]:
        #     e.bind('<FocusOut>', self.__event_range_input_lat)
        #     e.bind('<Return>',  self.__event_range_input_lat)
        #     # e.bind('<FocusOut>', self.__check_input)
        #     # e.bind('<Return>', self.__check_input)

        self.button_send = Button(self.frame_range, width=7, command=self.__callback_send_require, text='发送')
        self.button_send.grid(row=3, column=1, columnspan=2, padx=5, pady=20)

    # def __event_email_check(self, event):
    #     print('email')
    #     print self.entry_leftlat.get()
    #     self.entry_leftlon.delete(0, 'end')
    #     tkMessageBox.showerror('Wrong','不是合法的输入')

    # def __event_range_input_lon(self, event, string):
    #     self.__check_input(self, event.get() , True)
    #     print('input')

    def __event_range_input(self, event):
        entry = event.widget

        gleft = [self.entry_leftlon, self.entry_leftlat]  # g means group
        gright = [self.entry_rightlon, self.entry_rightlat]

        g = gleft if entry in gleft else gright

        if entry in gleft:
            g = gleft
        elif entry in gright:
            g = gright

        if g[0].get() == "" and g[1].get() == "":
            return

        try:
            lon = -1
            lat = -1
            if g[0].get() != "":

                lon = self.__check_input(g[0].get(), True)
            if g[1].get() != "":

                lat = self.__check_input(g[1].get(), False)
            # if g[0].get() != "" and g[1].get() != "":
            #     i, j = self.__find_geocoordinates(lon, lat)

        except ValueError:
            # entry.delete(0, 'end')
            # tkMessageBox.showerror('Wrong', '不是合法的输入')
            if entry.get() != '':
                entry['bg'] = 'red'
            self.is_send = False

        except RuntimeError:
            # entry.delete(0, 'end')
            # tkMessageBox.showerror('Wrong', '经纬度不在范围内')
            if entry.get() != '':
                entry['bg'] = 'red'
            self.is_send = False

        else:
            entry['bg'] = 'white'
            self.is_send = True

        # draw anyway even if exception
        # if g == gleft:
        #     self.__draw_left_point()
        # else:
        #     self.__draw_right_point()

    # def __event_range_input_lat(self, event, string):
    #     print('event.get()', event.get())
    #     self.__check_input(self, event.get(), False)
    #     print('input')


    def __callback_send_require(self):
        # if not self.is_send:
        #     tkMessageBox.showerror('Error', '存在不合法输入！')
        #     return

        receive = 'PolarReceiveReq@lamda.nju.edu.cn'
        # content = 'test'
        # send_mail.send(receive, content)

        self.w_long = self.__check_input(self.entry_leftlon.get(), True)
        self.e_long = self.__check_input(self.entry_rightlon.get(), True)
        self.n_lati = self.__check_input(self.entry_leftlat.get(), False)
        self.s_lati = self.__check_input(self.entry_rightlat.get(), False)
        # if (self.n_lati < self.s_lati):
        #     tkMessageBox.showerror('Wrong', '北纬需要大于南纬')
        # else:
        subject = ('[south]' +  str(self.w_long) +  ' ' +  str(self.e_long) +  ' ' +  str(self.n_lati) + ' ' + str(self.s_lati))
        ifsucss = send_mail.send(receive, subject)
        if(ifsucss):
            tkMessageBox.showinfo( 'info','发送成功')
            root.destroy()
        else:
            tkMessageBox.showerror('Wrong', '邮件发送失败，请检查网络')

    def __check_input(self, string, is_lon):
        value = -1

        pattern1 = '^[+-]?\d{1,3} \d{1,2} \d{1,2} ?$'
        pattern2 = '^[+-]?\d{1,3}\.?\d*$'

        if re.match(pattern1, string) != None:  # degree, minute, second
            values = string.split(' ')

            if float(values[1]) >= 60.00 or float(values[1]) < 0.00 or float(values[2]) >= 60.00 or float(
                    values[2]) < 0.00:
                raise RuntimeError('Out of range')
            if is_lon:
                if float(values[0]) > 179.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise RuntimeError('Out of range')
                    if float(values[1]) > 180.00:
                        raise RuntimeError('Out of range')
                if float(values[0]) < -179.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise RuntimeError('Out of range')
                    if float(values[1]) < -180.00:
                        raise RuntimeError('Out of range')
            else:
                if float(values[0]) > 89.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise RuntimeError('Out of range')
                    if float(values[1]) > 90.00:
                        raise RuntimeError('Out of range')
                if float(values[0]) < -89.00:
                    if float(values[1]) > 0.00 and float(values[2]) > 0.00:
                        raise RuntimeError('Out of range')
                    if float(values[1]) < -90.00:
                        raise RuntimeError('Out of range')
            if float(values[0]) > 0:
                value = float('%.2f' % (float(values[0]) + float(values[1]) / 60.00 + float(values[2]) / 3600.00))
            else:
                value = float('%.2f' % (float(values[0]) - float(values[1]) / 60.00 - float(values[2]) / 3600.00))
        elif re.match(pattern2, string) != None:  # float
            value = float('%.2f' % float(string))
            if is_lon:
                if value > 180.00 or value < -180.00:
                    raise RuntimeError('Out of range')
            else:
                if value > 90.00 or value < -90.00:
                    raise RuntimeError('Out of range')
        else:
            raise ValueError('Illegal input')

        return value

if __name__ == '__main__':
    root = Tk()
    root.title('Send Request')
    root.resizable(width=False, height=False)
    root.geometry("400x170")

    window = PointWindow(root)
    window.mainloop()
