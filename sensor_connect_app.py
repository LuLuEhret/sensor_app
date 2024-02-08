# %% Imports and global variables

import tkinter as tk
from tkinter import ttk
from pymodbus.client import ModbusSerialClient as ModbusClient
import serial.tools.list_ports
import log_functions as log_fct
import datetime as dt
import sys
import contextlib
import io
from tkinter import Text, Scrollbar

captured_output = io.StringIO()

NO_ERROR = 0
ERROR = 1
VALUE = 0
ERROR_MSG = 1
ready_to_connect = False
continuous_reading = False
waiting_screen = True
baudrate = 9600
parity = "N"
ID_slave = 1


# %% Functions
def clear_output():
    output_entry.config(state="normal")
    output_entry.delete("1.0", tk.END)
    output_entry.config(state="disabled")


def handle_key_event(event):
    # Check if the event corresponds to a specific keyboard shortcut
    if event.keysym == "Return":
        # Call the button click function
        client_generator()
        # print("Keyboard shortcut pressed")


def scan_com_ports():
    com_ports = list(serial.tools.list_ports.comports())
    com_port_list = [port.device for port in com_ports]
    com_port_list.append("COM test")
    return com_port_list


def init_modbus_client(portname, baudrate, parity):
    # global client
    client = ModbusClient(
        # client = ModbusSerialClient(
        port=portname,
        stopbits=1,
        bytesize=8,
        baudrate=int(baudrate),
        parity=parity,
        timeout=0.4,
    )
    return client


def check_id_entry(id_entered):
    """
    Check if the ID entered is a number and if it is between 0 and 255
    """
    # check if the input is a number
    if id_entered.isnumeric() and int(id_entered) < 256:
        return [int(id_entered), NO_ERROR]
    else:
        # print("Please enter a number")
        return [None, ERROR]


def check_port(port_entered):
    """
    Check if the port entered is a COM port, different from the COM test
    """
    if port_entered != "Select a COM Port":  # and port_entered != "COM test":
        return [port_entered, NO_ERROR]
    else:
        return ["No port", ERROR]


def warning_message_input(port, id, baud, parity):
    """
    Set the warning message depending on the errors detected
    """
    msg = "Error with: "
    error = False
    if port[ERROR_MSG] == ERROR:
        msg += "port "
        error = True
    if id[ERROR_MSG] == ERROR:
        if error:
            msg += ", "
        msg += "ID"
        error = True
    if not error:
        msg = (
            "Client created with: "
            + port[VALUE]
            + ", "
            + str(baud)
            + ", "
            + parity
            + ", "
            + str(id[VALUE])
        )

    # print(msg)
    return [msg, error]


def open_secondary_window():
    def on_window_close():
        nonlocal client_modbus
        client_modbus.close()
        secondary_window.destroy()

    def update_tree_values(reg_entry_number=20):
        nonlocal time_passed
        nonlocal client_modbus
        if (
            reg_entry.get().isnumeric()
            and reg_entry.get() != ""
            and int(reg_entry.get()) <= 100
        ):
            reg_entry_number = int(reg_entry.get())
        else:
            reg_entry_number = 5
        values_reg = []
        for item in tree.get_children():
            tree.delete(item)
        try:
            values_reg = client_modbus.read_holding_registers(
                address=0, count=reg_entry_number, slave=selected_id
            ).registers
        except:
            client_modbus.close()
        # print(values_reg)
        if values_reg == []:
            values_reg = ["xxx" for i in range(reg_entry_number)]
        for i in range(reg_entry_number):
            if i % 2 == 0:
                tree.insert("", i, values=(i, values_reg[i]), tags=("Cl2"))
            else:
                tree.insert("", i, values=(i, values_reg[i]), tags=("Cl1"))
        time_passed = time_passed + 1
        time_label.config(text="Time: " + str(time_passed) + " sec")
        tree.after(1000, update_tree_values, reg_entry_number)

    time_passed = 0
    selected_id = check_id_entry(id_entry.get())[VALUE]
    secondary_window = tk.Toplevel()
    secondary_window.title("Secondary Window")
    secondary_window.geometry("270x480")
    secondary_window.resizable(False, False)
    secondary_window.protocol("WM_DELETE_WINDOW", on_window_close)
    reg_label = ttk.Label(secondary_window, text="Nb reg to read: ")
    reg_label.grid(row=0, column=0, padx=10, pady=10)
    reg_entry = ttk.Entry(secondary_window, width=5)
    reg_entry.insert(0, "15")
    reg_entry.grid(row=0, column=1, pady=10)
    time_label = ttk.Label(secondary_window, text="Time: 0 sec")
    time_label.grid(row=0, column=2, pady=10, padx=10)

    tree_frame = ttk.Frame(secondary_window)
    tree_frame.grid(row=1, column=0, columnspan=4, rowspan=10, sticky="WENS")

    tree = ttk.Treeview(tree_frame, height=20, selectmode="browse")
    tree.pack(expand=True, fill="x", padx=10)

    # Define columns
    tree["columns"] = ("Reg", "Value")

    # Format columns
    tree.column("#0", width=0, stretch=tk.NO)  # Invisible main column
    tree.column("Reg", anchor=tk.W, width=50)
    tree.column("Value", anchor=tk.W, width=150)

    # Create headings
    tree.heading("#0", text="", anchor=tk.W)
    tree.heading("Reg", text="Register", anchor=tk.W)
    tree.heading("Value", text="Value", anchor=tk.W)

    # Set treeview row font color or foreground color
    tree.tag_configure("Cl1", background="white", foreground="black")
    tree.tag_configure("Cl2", background="#d9d9d9", foreground="black")
    client_modbus = init_modbus_client(
        check_port(com_port_combobox.get())[VALUE], baudrate, parity
    )
    tree.after(1000, update_tree_values, int(reg_entry.get()))


# %% Main functions

function_list_log = [
    getattr(log_fct, name)
    for name in dir(log_fct)
    if callable(getattr(log_fct, name)) and name.startswith("log")
]
function_list_log = [func.__name__ for func in function_list_log]
function_list_log = ["Please select one !"] + function_list_log
function_list_basic = [
    "Please select one !",
    "read_holding_registers",
    "read_input_registers",
]

function_list_setup = [
    getattr(log_fct, name)
    for name in dir(log_fct)
    if callable(getattr(log_fct, name)) and name.startswith("setup")
]
function_list_setup = [func.__name__ for func in function_list_setup]
function_list_basic_setup = ["write_register"]


def client_generator():
    """
    Check if the input is correct to generate the client
    """
    global ready_to_connect, baudrate, parity, ID_slave
    selected_port = check_port(com_port_combobox.get())
    selected_baudrate = int(baudrate_combobox.get())
    selected_parity = parity_combobox.get()
    selected_id = check_id_entry(id_entry.get())
    label_message.config(
        text=warning_message_input(
            selected_port, selected_id, selected_baudrate, selected_parity
        )[VALUE]
    )

    if not warning_message_input(
        selected_port, selected_id, selected_baudrate, selected_parity
    )[ERROR_MSG]:
        label_image.config(image=img_check)
        ready_to_connect = True
        baudrate = selected_baudrate
        parity = selected_parity
        ID_slave = selected_id[VALUE]
        secondary_window_button["state"] = "normal"
        if rad_butt_var.get():
            read_button["state"] = "normal"

    else:
        label_image.config(image=img_cross)
        ready_to_connect = False
        read_button["state"] = "disabled"
        secondary_window_button["state"] = "disabled"
    return None


def cont_reading():
    """
    Used to read the data continuously
    """
    global continuous_reading
    continuous_reading = True
    update_value()


def single_reading():
    """
    Read the data once
    """
    global continuous_reading
    continuous_reading = False
    update_value()


def update_value():
    """
    Called to update the value of the data
    """
    global continuous_reading
    slave_id = check_id_entry(id_entry.get())
    address_to_read_from = check_id_entry(address_entry.get())
    text_to_display = read_register_log(function_combobox.get(), slave_id[VALUE], address_to_read_from[VALUE]) + ["@", str(dt.datetime.now().strftime("%H:%M:%S"))]
    text_to_display = " ".join(text_to_display)
    data_value_lbl.config(text=text_to_display)

    if continuous_reading:
        # update_output(captured_output.getvalue())
        data_value_lbl.after(1000, update_value)
    return True


def write_value():
    """
    Used to write the value in the sensor
    """
    slave_id = check_id_entry(id_entry.get())
    write_register_setup(function_combobox_setup.get(), slave_id[VALUE])
    return True


def write_value_basic():
    """
    Used to write the value in the sensor, but with the basic functions
    """
    slave_id = check_id_entry(id_entry.get())
    address_to_write = address_entry_2.get()
    # check if the input is a number
    if address_to_write.isnumeric():
        address_to_write = int(address_to_write)
        print(function_combobox_setup_basic.get())
        write_register_setup(
            function_combobox_setup_basic.get(), slave_id[VALUE], address_to_write
        )
    else:
        write_lbl.config(text="Error")
    return True


def read_register_log(function_log, ID_slave, address_to_read_from=0):
    """
    Functions that reads the data from the sensor, depending on the function selected
    """
    values_reg = []
    global baudrate, parity
    client_modbus = init_modbus_client(
        check_port(com_port_combobox.get())[VALUE], baudrate, parity
    )
    if function_log == "log_apogee_GHI":
        try:
            values_reg = [log_fct.log_apogee_GHI(client_modbus, ID_slave)]
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "log_par":
        try:
            values_reg = [log_fct.log_par(client_modbus, ID_slave)]
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "log_th":
        try:
            values_reg = [log_fct.log_th(client_modbus, ID_slave)]
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "log_ir_leaf_temp":
        try:
            values_reg = [log_fct.log_ir_leaf_temp(client_modbus, ID_slave)]
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "log_dustIQ":
        try:
            values_reg = [log_fct.log_dustIQ(client_modbus, ID_slave)]
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "log_wspeed":
        try:
            values_reg = [log_fct.log_wspeed(client_modbus, ID_slave)]

        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "log_wspeed_ultrasonic":
        try:
            values_reg = [log_fct.log_wspeed_ultrasonic(client_modbus, ID_slave)]
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "log_rainfall":
        try:
            values_reg = [log_fct.log_rainfall(client_modbus, ID_slave)]
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "read_holding_registers":
        try:
            values_reg = client_modbus.read_holding_registers(
                address=address_to_read_from, count=1, slave=ID_slave
            ).registers
        except:
            values_reg = ["error"]
            client_modbus.close()

    elif function_log == "read_input_registers":
        try:
            values_reg = client_modbus.read_input_registers(
                address=address_to_read_from, count=1, slave=ID_slave
            ).registers
        except:
            values_reg = ["error"]
            client_modbus.close()

    else:
        values_reg = ["error"]
    values_reg = [str(i) for i in values_reg]
    client_modbus.close()
    return values_reg



def write_register_setup(fct_setup, slave_id, address_to_write=0):
    """
    Functions that writes the data from the sensor, depending on the function selected
    """
    client_modbus = init_modbus_client(
        check_port(com_port_combobox.get())[VALUE],
        baudrate_combobox.get(),
        parity_combobox.get(),
    )
    if fct_setup == "setup_par_id":
        value_to_write = int(value_entry.get())
        log_fct.setup_par_id(client_modbus, value_to_write, slave_id)

    elif fct_setup == "setup_th_id":
        value_to_write = int(value_entry.get())
        log_fct.setup_th_id(client_modbus, value_to_write, slave_id)

    elif fct_setup == "setup_ir_leaf_temp_id":
        value_to_write = int(value_entry.get())
        try:
            log_fct.setup_ir_leaf_temp_id(client_modbus, value_to_write, slave_id)
        except:
            write_lbl.config(text="Error")
            return None

    elif fct_setup == "setup_ir_leaf_temp_emissivity":
        value_to_write = int(value_entry.get())
        try:
            log_fct.setup_ir_leaf_temp_emissivity(
                client_modbus, value_to_write, slave_id
            )
        except:
            write_lbl.config(text="Error")
            return None

    elif fct_setup == "setup_wind_speed_id":
        value_to_write = int(value_entry.get())
        try:
            log_fct.setup_wind_speed_id(client_modbus, value_to_write, slave_id)
        except:
            write_lbl.config(text="Error")
            return None

    elif fct_setup == "setup_wind_speed_ultrasonic_id":
        value_to_write = int(value_entry.get())
        try:
            log_fct.setup_wind_speed_ultrasonic_id(client_modbus, value_to_write, slave_id)
        except:
            write_lbl.config(text="Error")
            return None

    elif fct_setup == "write_register":
        value_to_write_2 = int(value_entry_2.get())
        try:
            client_modbus.write_register(
                address=address_to_write, value=value_to_write_2, slave=ID_slave
            )
        except:
            write_lbl.config(text="Error")
            print("error")
            return None

    else:
        return ["error"]
    write_lbl.config(text="✅")
    # after 2 seconds, reset the label
    write_lbl.after(4000, lambda: write_lbl.config(text="   "))
    client_modbus.close()
    return None


def change_combobox_state(*args):
    """
    Toggles the state of the comboboxes depending on the radiobutton selected
    """
    global ready_to_connect
    if rad_butt_var.get():  # Check the value of the Radiobutton
        function_combobox["state"] = "normal"
        if ready_to_connect:
            read_button["state"] = "normal"
            read_button_single["state"] = "normal"
    else:
        function_combobox.set("Select a function")
        function_combobox["state"] = "disabled"
        read_button["state"] = "disabled"
        read_button_single["state"] = "disabled"
        secondary_window_button["state"] = "disabled"


def change_combobx_entries():
    """
    Changes the entries of the comboboxes depending on the radiobutton selected
    """
    if rad_butt_var.get() == 1:  # Check the value of the Radiobutton
        function_combobox["values"] = function_list_log
        function_combobox.current(0)
    elif rad_butt_var.get() == 2:
        function_combobox["values"] = function_list_basic
        function_combobox.current(0)
    else:
        function_combobox["values"] = []


def reset_combobox_data_text(event):
    """
    Set the text of the combobox to nothing when the combo box stated is changed
    """
    function_combobox.set("")


def display_info_box_in(event):
    radio_1.config(text="Log fct")


def display_info_box_out(event):
    radio_1.config(text="")


def change_combobox_setup_state(*args):
    global ready_to_connect
    # change the state of the comboboxes
    if rad_butt_var_setup.get() == 1:
        if ready_to_connect:
            function_combobox_setup["state"] = "normal"
            write_button["state"] = "normal"
        function_combobox_setup_basic["state"] = "disabled"
        write_button_2["state"] = "disabled"
    elif rad_butt_var_setup.get() == 2:
        function_combobox_setup["state"] = "disabled"
        write_button["state"] = "disabled"
        if ready_to_connect:
            function_combobox_setup_basic["state"] = "normal"
            write_button_2["state"] = "normal"
    else:
        function_combobox_setup["state"] = "disabled"
        function_combobox_setup_basic["state"] = "disabled"
        write_button["state"] = "disabled"
    return None


def change_setup_combobox_entries():
    return None


# %% Main window
# ----------------------------------main window-----------------------------------------#

root = tk.Tk()
root.title("Modbus sensor connection app")

root.geometry("650x400")
root.resizable(False, True)
root.configure(background="white")

img_check = tk.PhotoImage(file="images/check.png")
img_cross = tk.PhotoImage(file="images/cross.png")
img_loading = tk.PhotoImage(file="images/loading.gif")
img_label = tk.PhotoImage(file="images/label_bg.png")

label_input = ttk.Label(root, text="Client creation")
label_input.configure(background="white")
label_input.pack(side="top", padx=10, fill="x")
# label_input.grid(row=0, column=0, padx=10, pady=0, sticky="w")


# %% Frame : input
# ----------------------------------input frame-----------------------------------------#

# Create a frame for the ComboBoxes and place it at the top of the window
combobox_frame = ttk.Frame(root)
combobox_frame.pack(side="top", padx=10, pady=10, fill="x")
combobox_frame["borderwidth"] = 5
combobox_frame["relief"] = "groove"

# Create ComboBoxes for COM ports, baud rates, and parities
com_port_list = scan_com_ports()
com_port_combobox = ttk.Combobox(combobox_frame, values=com_port_list)
com_port_combobox.set(com_port_list[0])

baudrate_list = ["9600", "19200", "38400", "57600", "115200"]
baudrate_combobox = ttk.Combobox(combobox_frame, values=baudrate_list, width=10)
baudrate_combobox.current(0)

parity_list = ["N", "E", "O"]
parity_combobox = ttk.Combobox(combobox_frame, values=parity_list, width=5)
parity_combobox.current(0)

com_port_combobox.pack(side="left", padx=10)
baudrate_combobox.pack(side="left", padx=10)
parity_combobox.pack(side="left", padx=10)

# Create a text box for manually entering the ID
id_label = ttk.Label(combobox_frame, text="Slave ID:")
id_label.pack(side="left", padx=10)

id_entry = ttk.Entry(combobox_frame, width=5)
id_entry.pack(side="left", padx=10)
id_entry.insert(0, "1")


label_state = ttk.Label(root, text="State")
label_state.pack(side="top", padx=10, fill="x")
# label_state.grid(row=2, column=0, padx=10, pady=0, sticky="w")
label_state.configure(background="white")

# Add a button on the right of the frame, that confirms the selection
client_button = ttk.Button(combobox_frame, text="Apply", command=client_generator)
client_button.pack(side="right", padx=10)


# %% Frame : message

message_frame = ttk.Frame(root)
message_frame.pack(side="top", padx=10, pady=10, fill="x")
message_frame["borderwidth"] = 5
message_frame["relief"] = "groove"

label_message = ttk.Label(
    message_frame, background="#D5D5D5", width=50, text="Warnings and messages",
    font=("Arial", 12),
    borderwidth=2,
    relief="solid",  # Other options: "flat", "raised", "sunken", "ridge", "groove"
)
label_message.pack(side="left", padx=10)


label_image = ttk.Label(message_frame, image=img_loading)
label_image.pack(side="right", padx=10)


# %% Frame : data
r = 0
c = 0


label_data = ttk.Label(root, text="Data reading")
label_data.pack(side="top", padx=10, anchor="w")
label_data.configure(background="white")


data_frame = ttk.Frame(root)
data_frame.pack(side="top", padx=10, pady=10, fill="x")

data_frame["borderwidth"] = 5
data_frame["relief"] = "groove"


rad_butt_var = tk.IntVar()

# rewrite the radiobuttons without the loop
radio_1 = tk.Radiobutton(
    data_frame,
    text="Log fct",
    variable=rad_butt_var,
    value=1,
    command=change_combobx_entries,
)
radio_1.grid(row=r, column=c, padx=0, pady=0, sticky="w")
radio_1.bind("<Button-1>", reset_combobox_data_text)

radio_2 = tk.Radiobutton(
    data_frame,
    text="Basic fct",
    variable=rad_butt_var,
    value=2,
    command=change_combobx_entries,
)
radio_2.grid(row=(r := r + 1), column=c, padx=0, pady=0, sticky="w")
radio_2.bind("<Button-1>", reset_combobox_data_text)

rad_butt_var.trace("w", change_combobox_state)


# add a combo box to choose the function to use from the list
# function_list = [func for name, func in globals().items() if callable(func) and name.startswith("log")]
function_combobox = ttk.Combobox(
    data_frame, values=function_list_log, width=20, state="disabled"
)
function_combobox.set("Select a function")
# function_combobox.pack(side="left", padx=10)
function_combobox.grid(row=0, column=1, padx=10, pady=0, columnspan=2)


# add an entry to choose the adress to read from
address_label = ttk.Label(data_frame, text="Adr (basic fct):")
address_label.grid(row=1, column=1, padx=10, pady=0)

# add an entry to choose the adress to read from
address_entry = ttk.Entry(data_frame, width=5)
address_entry.grid(row=1, column=2, padx=10, pady=0)


# add a button to update the data using the function above
read_button = ttk.Button(
    data_frame, text="Read continuous", command=cont_reading, state="disabled"
)
read_button.grid(row=0, column=3, padx=10, pady=0)

# add a button for update the data using the function above
read_button_single = ttk.Button(
    data_frame, text="Read once", command=single_reading, state="disabled", width=15
)
read_button_single.grid(row=1, column=3, padx=10, pady=0)

# add a label for the data
data_label = ttk.Label(data_frame, text="Data:")
data_label.grid(row=0, column=4, padx=10, pady=0, rowspan=2)


# # add a label for the data
# data_value_lbl = ttk.Label(
#     data_frame, text=rad_butt_var.get(), background="#D5D5D5", font=("Arial", 13)
# )
# data_value_lbl.grid(row=0, column=5, padx=10, pady=0, rowspan=2)
# data_value_lbl.config(wraplength=200)
# Add a label for the data
data_value_lbl = ttk.Label(
    data_frame,
    # text=rad_butt_var.get(),
    text="                                                                  ",
    background="#D5D5D5",
    font=("Arial", 13),
    borderwidth=2,
    relief="solid",  # Other options: "flat", "raised", "sunken", "ridge", "groove"
)
data_value_lbl.grid(row=0, column=5, padx=10, pady=0, rowspan=2, sticky="nsew")  # Use sticky to fill the available space
data_value_lbl.config(wraplength=200)

# # add a label for the data
# data_unit = ttk.Label(data_frame, text="(unit)")
# data_unit.grid(row=0, column=6, padx=10, pady=0, rowspan=2)


# add a button on the right of the frame, that opens a new window
secondary_window_button = ttk.Button(
    root, text=" Read all registers", command=open_secondary_window, state="disabled"
)
secondary_window_button.pack(side="top", padx=10, pady=0, anchor="e")

# %% Frame : setup
# ----------------------------------setup frame-----------------------------------------#

setup_frame_lbl = ttk.Label(root, text="Setup sensor")
setup_frame_lbl.pack(side="top", padx=10, fill="x")
# setup_frame_lbl.grid(row=6, column=0, padx=10, pady=0, sticky="w")
setup_frame_lbl.configure(background="white")
setup_frame = ttk.Frame(root)
setup_frame.pack(side="top", padx=10, pady=10, fill="x")
# setup_frame.grid(row=7, column=0, padx=10, pady=0, sticky="w")
setup_frame["borderwidth"] = 5
setup_frame["relief"] = "groove"

rad_butt_var_setup = tk.IntVar()

radio_setup_1 = tk.Radiobutton(
    setup_frame,
    text="Setup fct",
    variable=rad_butt_var_setup,
    value=1,
    command=change_setup_combobox_entries,
)
radio_setup_1.grid(row=0, column=0, padx=10, pady=0)
radio_setup_2 = tk.Radiobutton(
    setup_frame,
    text="Basic fct",
    variable=rad_butt_var_setup,
    value=2,
    command=change_setup_combobox_entries,
)
radio_setup_2.grid(row=1, column=0, padx=10, pady=0)
# add a trace
rad_butt_var_setup.trace("w", change_combobox_setup_state)

# add a combo box to choose the function to use from the list

function_combobox_setup = ttk.Combobox(
    setup_frame, values=function_list_setup, width=20, state="disabled"
)
function_combobox_setup.set("Select a function")
function_combobox_setup.grid(row=0, column=1, padx=10, pady=0)

function_combobox_setup_basic = ttk.Combobox(
    setup_frame, values=function_list_basic_setup, width=20, state="disabled"
)
function_combobox_setup_basic.set("Select a function")
function_combobox_setup_basic.grid(row=1, column=1, padx=10, pady=0)


# add a label that says "Val: "
value_label = ttk.Label(setup_frame, text="Val: ")
value_label.grid(row=0, column=2, padx=10, pady=0)

# add a text entry for the value to write
value_entry = ttk.Entry(setup_frame, width=5)
value_entry.grid(row=0, column=3, padx=10, pady=0)

# add a button to update the data using the function above
write_button = ttk.Button(
    setup_frame, text="Write value", command=write_value, state="disabled"
)
write_button.grid(row=0, column=7, padx=10, pady=0)

# add a label that says "Val: "
value_label = ttk.Label(setup_frame, text="Val: ")
value_label.grid(row=1, column=2, padx=10, pady=0)

# add a text entry for the value to write
value_entry_2 = ttk.Entry(setup_frame, width=5)
value_entry_2.grid(row=1, column=3, padx=10, pady=0)

# add a label that says "Val: "
value_label = ttk.Label(setup_frame, text="Adr: ")
value_label.grid(row=1, column=4, padx=10, pady=0)

# add a text entry for the address to write to
address_entry_2 = ttk.Entry(setup_frame, width=5)
address_entry_2.grid(row=1, column=6, padx=10, pady=0)

# add a button to update the data using the function above
write_button_2 = ttk.Button(
    setup_frame, text="Write value", command=write_value_basic, state="disabled"
)
write_button_2.grid(
    row=1,
    column=7,
    padx=10,
    pady=0,
)

# add a label that shows the if the write was successful
write_lbl = ttk.Label(setup_frame, text="   ")
write_lbl.grid(row=0, column=8, padx=10, pady=0, sticky="WENS")


# # %% Frame : output from python script
# # ----------------------------------output frame-----------------------------------------#
# # add a label that says "Output of the script: ""bo
# output_label = ttk.Label(root, text="Error messages ")
# output_label.pack(side="top", padx=10, fill="x")
# #replace pack by grid
# # output_label.grid(row=0, column=0, padx=10, pady=0, sticky="w")
# output_label.configure(background="white")

# output_frame = ttk.Frame(root)
# output_frame.pack(side="top", padx=10, pady=10, fill="x")
# #replace pack by grid
# # output_frame.grid(row=1, column=0, padx=10, pady=0, sticky="w")
# output_frame["borderwidth"] = 1
# output_frame["relief"] = "groove"

# # # add entry widget to display the output, and make it scrollable
# # output_entry = ttk.Entry(output_frame, textvariable="")
# # output_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True, ipady=30)
# # output_scroll = ttk.Scrollbar(output_frame, orient="vertical", command=output_entry.xview)
# # output_scroll.pack(side="right", fill="y")
# # output_entry.config(xscrollcommand=output_scroll.set, state='readonly', background="white", )

# # add a button below the entry widget to clear the output
# clear_button = ttk.Button(output_frame, text="Clear", command=clear_output)
# # clear_button.pack(side="top", padx=0, pady=5)
# #replace pack by grid
# clear_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")

# output_entry = Text(output_frame, wrap="word", height=5, width=57, state="disabled")
# # output_entry.pack(side="left", padx=10, pady=10, fill="x")
# #replace pack by grid
# output_entry.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
# output_scroll = Scrollbar(output_frame, orient="vertical", command=output_entry.yview)
# # output_scroll.pack(side="right", fill="y")
# #replace pack by grid
# output_scroll.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
# output_entry.config(
#     yscrollcommand=output_scroll.set,
#     state="disabled",
#     background="white",
#     padx=5,
#     pady=5,
# )





# %% Main loop
# ----------------------------------main loop-----------------------------------------#
frameCnt = 12
frames = [
    tk.PhotoImage(file="images/loading.gif", format="gif -index %i" % (i))
    for i in range(frameCnt)
]


def update_gif(ind):
    global ready_to_connect
    frame = frames[ind]
    ind += 1
    if ind == frameCnt:
        ind = 0
    if not ready_to_connect:
        label_image.configure(image=frame)
        root.after(100, update_gif, ind)


# def update_output(text_var):
#     # print("update output")
#     output_entry.config(state="normal")
#     output_entry.delete(0, tk.END)
#     output_entry.insert(tk.END, text_var)
#     # print(text_var)
#     output_entry.config(state='disabled')
#     root.after(1000, update_output, captured_output.getvalue())

# def update_output(text_var):
#     # print("update output")
#     # print("error: ", text_var)
#     output_entry.config(state="normal")
#     output_entry.delete("1.0", tk.END)
#     output_entry.insert(tk.END, text_var)
#     output_entry.config(state='disabled')
#     # sys.stdout.flush()
#     # root.after(1000, update_output, captured_output.getvalue())



# with contextlib.redirect_stdout(captured_output):
#     root.after(0, update_gif, 0)
#     root.after(200, update_output, captured_output.getvalue())
#     # Start the Tkinter main loop
#     root.bind("<Return>", handle_key_event)
#     root.mainloop()

root.after(0, update_gif, 0)
root.bind("<Return>", handle_key_event)
root.mainloop()
