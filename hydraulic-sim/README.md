# Flower sim
This package simulates the serial interface the flower model is going talk to.
The actual hydraulic controller is going to read from a serial connection. This is a model which will help me design the responses the flower brain is gonna generate. Since we have to take into account the speed that the cylinder can move at.


## Communication spec
The controller expects a `set-point` for the cylinder, which is a ranging `0-100`. Instead of the `set-point` we can also send it `???` upon which the controller will reply with the current position.

The controller will: 
1. Move the cylinder to `set-point` position
2. Hold it there.
3. Wait for a new command.

