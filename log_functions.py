import struct
from pymodbus.client import ModbusSerialClient as ModbusClient


"""
Log function need to start with "log" to be recognized by the main program
Setup functions need to start with "setup" to be recognized by the main program

"""



def list_formatting(liste):
    """
    input: list
    output: formatted string
    """
    formatted_string = " ".join(str(item) for item in liste)
    return formatted_string

def int_to_float32(int16_1, int16_2):
    """
    Convert two 16-bit integers to a 32-bit float
    input: two 16-bit integers
    output: 32-bit float
    """
    # Pack the two 16-bit integers into a 32-bit binary representation
    int32_value = (int16_1 << 16) | int16_2
    # Convert the 32-bit integer to a float32
    float32_bytes = struct.pack('I', int32_value)  # 'I' format for unsigned int
    float32_value = struct.unpack('f', float32_bytes)[0]

    # print(f"Input Unsigned Integers: {int16_1}, {int16_2}")
    # print(f"Unsigned Float32 Value: {float32_value}")
    return float32_value


def log_apogee_GHI(client_local, slave_id):
    """
    Communicate and read from the Apogee GHI sensor
    input: modbus client; sensor address
    output: GHI in µmol/m2/s
    """
    # client.connect()
    raw_data = client_local.read_holding_registers(address=0, count=50, slave_id=slave_id).registers
    # raw_data = read_holding_registers_(client=client_local, address=0, count=50, slave_id=slave_id)
    watt_float = int_to_float32(raw_data[0], raw_data[1])
    # client.close()
    # watt_from_lib = decode_32bits(res, 0)
    return watt_float


def log_par(client_local: ModbusClient, slave_id: int):
    """
    Communicate and read from the Par sensor
    input: modbus client; sensor address
    output: par radiation in µmol/m2/s and in Watt
    """
    raw_data = client_local.read_holding_registers(address=0, count=2, slave=slave_id).registers
    # raw_data = read_holding_registers_(client=client_local, address=0, count=2, slave_id=slave_id)
    radiation_mol = raw_data[0]
    radiation_watt = raw_data[1]
    liste = ["Radiation (µmol/m2/s): ", radiation_mol, " ,Radiation (W/m2): ", radiation_watt]
    return list_formatting(liste)

def log_th(client_local: ModbusClient, slave_id: int):
    """
    Communicate and read from the Ambient T/H sensor
    input: modbus client; sensor address
    output: Ambient T (ºC) and H (%)
    """
    raw_data = client_local.read_holding_registers(address=0, count=2, slave=slave_id).registers
    # raw_data = read_holding_registers_(client=client_local, address=0, count=2, slave_id=slave_id)
    # raw_data = client_local.read_holding_registers(6, 1, slave=slave_id)
    temperature = (raw_data[0]) / 10
    humidity = (raw_data[1]) / 10
    liste = ["Temperature: ", temperature, " ,Humidity: ", humidity]
    return list_formatting(liste)


def log_ir_leaf_temp(client_local:ModbusClient ,slave_id: int):
    """
    Communicate and read from the IR leaf temperature sensor
    input: modbus client; sensor address
    output: Filtered Temp (°C)
    """
    raw_data = client_local.read_holding_registers(0x0b, 1, slave=slave_id).registers[0]
    raw_data = raw_data / 10
    return raw_data

def log_dustIQ(client_local:ModbusClient, slave_id: int):
    """
    Communicate and read from the DustIQ sensor
    input: modbus client; sensor address
    output: Transmission (%)
    """
    raw_data = client_local.read_input_registers(0, 50, slave=slave_id).registers
    SR_sensor_1 = raw_data[20]/10
    TR_loss_1 = raw_data[21]/10
    SR_sensor_2 = raw_data[24]/10
    TR_loss_2 = raw_data[25]/10
    tilt_x = raw_data[28]
    tilt_y = raw_data[29]
    temp_backpanel = raw_data[31]
    status_flag = raw_data[34]
    # liste = ["SR1:",SR_sensor_1,"TR1:", TR_loss_1, "\nSR2:",SR_sensor_2, "TR2:",TR_loss_2, "\ntilt_x:",tilt_x, 
    #          "tilt_y:",tilt_y, "\ntemp:",temp_backpanel, "status:",bin(status_flag)]
    # return list_formatting(liste)  
    return SR_sensor_1, TR_loss_1, SR_sensor_2, TR_loss_2


def setup_par_id(client: ModbusClient, new_slave_id: int, current_slave_id: int = 0):
    """
    input: modbus client; future address
    output: the address of the slave gets changed
    """
    return client.write_register(address=0x42, value=new_slave_id, slave=current_slave_id)


def setup_th_id(client: ModbusClient, new_slave_id: int, current_slave_id: int = 254):
    """
    input: modbus client; future address
    output: the address of the slave gets changed
    """
    return client.write_register(address=0x00, value=new_slave_id, slave=current_slave_id)



def setup_ir_leaf_temp_id(client: ModbusClient, new_slave_id: int, current_slave_id: int):
    """
    input: modbus client; future address
    output: the address of the slave gets changed
    """
    cmds = {
        "slave_id": 0x04,
        "AVG": 0x0A,  # Max val = 60 seconds
        "Hold": 0x08,
    }
    adr = cmds["slave_id"]
    return client.write_register(address=adr, value=new_slave_id, slave=current_slave_id)
    # assert [new_slave_id] == read_holding_registers(client=client, address=adr, count=1, slave_id=current_slave_id), "Slave ID not set"


def setup_ir_leaf_temp_emissivity(client: ModbusClient, emissivity:int, slave_id: int):
    """
    input: modbus client; emissivity value
    output: the emissivity value gets changed
    """
    return client.write_register(address=0x17, value=emissivity, slave=slave_id)