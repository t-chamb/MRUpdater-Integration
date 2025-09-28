---
inclusion: manual
---

# Chromatic Hardware Specifications

This document contains technical specifications discovered through reverse engineering analysis of ModRetro's open-source firmware. Use this information when implementing hardware communication and protocol layers.

## USB Device Specifications

### Device Identification
- **Vendor ID**: `0x374E` (ModRetro)
- **Product ID**: `0x013F` (Chromatic)
- **Device Class**: Composite USB Device

### USB Endpoints
- **EP0**: Control endpoint (standard USB control)
- **EP1**: Video Control (UVC interface)
- **EP2**: Video Stream (UVC interface for screen capture)
- **EP3**: Serial/UART (CDC-ACM interface) - **Primary interface for Cart Clinic**

### Communication Interface
Use **USB Endpoint 3** (CDC-ACM Serial) for all cartridge operations:
- Standard CDC-ACM driver compatibility
- Cross-platform support via Qt Serial Port
- No custom drivers required

## Hardware Architecture

### System Components
1. **ESP32 MCU**: System management, USB communication, user interface
2. **Gowin GW5A-25 FPGA**: Game Boy core, cartridge interface, USB device controller
3. **Cartridge Interface**: Direct electrical connection to Game Boy cartridge

### Communication Flow
```
PC Application → USB CDC-ACM (EP3) → ESP32 MCU → Custom UART → FPGA → Cartridge Interface
```

## Cartridge Interface Specifications

### Physical Interface Signals
- **CART_A[15:0]**: 16-bit address bus
- **CART_D[7:0]**: 8-bit bidirectional data bus
- **CART_CLK**: Clock signal (4MHz/8MHz modes)
- **CART_CS**: Chip select (active low)
- **CART_RD**: Read enable (active low)
- **CART_WR**: Write enable (active low)
- **CART_RST**: Reset signal
- **CART_DATA_DIR_E**: Data direction control
- **CART_DET**: Hardware cartridge detection

### Timing Characteristics
- Supports Game Boy CPU modes: 4MHz (normal) and 8MHz (double speed)
- Clock generation synchronized with Game Boy CPU states
- Independent cartridge access (can bypass Game Boy core)
- Proper setup/hold times maintained for cartridge compatibility

## Protocol Implementation Guidelines

### USB Communication
```cpp
// Device detection
QSerialPortInfo::availablePorts() // Filter by VID/PID
QSerialPort port;
port.setPortName(portName);
port.setBaudRate(QSerialPort::Baud115200); // Standard CDC-ACM
```

### Command Structure (To be discovered)
Based on analysis, expect packet structure similar to:
```
[Header] [Command] [Length] [Payload...] [Checksum]
```

### Error Handling
- USB disconnection detection
- Timeout handling for long operations
- Cartridge presence validation
- Firmware version compatibility checks

## Development Notes

### Source Code References
Key files from ModRetro's open-source firmware:
- `chromatic_mcu/main/fpga_tx.c`: MCU to FPGA communication
- `chromatic_mcu/main/fpga_rx.c`: FPGA to MCU communication
- `chromatic_fpga/src/rtl/USB/`: USB implementation
- `chromatic_fpga/src/rtl/EMU/cart.v`: Cartridge interface

### Testing Considerations
- Test with actual Chromatic hardware
- Verify cartridge detection and identification
- Test various Game Boy and Game Boy Color cartridge types
- Validate timing requirements for different MBC types

### Security and Safety
- Validate all memory addresses before access
- Implement proper error recovery for failed operations
- Respect cartridge write protection
- Handle power management states appropriately