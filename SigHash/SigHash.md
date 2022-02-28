# Bandera _SIGHASH_ 

Las firmas diditales se codifican en el formato _DER_ (Distinguished Encoding Rules), y se utiliza ampliamente en **Bitcoin**. El formato _DER_ se define de la siguiente manera:
1. Inicia con el byte _0x30_
2. _0x45_ que es la longitud total de la firma (69 bytes en decimal)
3. _0x02_ que indica que sigue un valor entero
4. _0x21_ la ongitud del entero (33 bytes en decimal)
5. El valor de _R_
6. _0x02_ que indica que sigue un valor entero
7. _0x20_ la ongitud del entero (32 bytes en decimal)
8. El valor de _S_
9. Un sufijo que indica el valor del SIGHASH a utilizar, por ejemplo _0x01_ (SIGHASH_ALL)

Las firmas digitales se aplican a mensajes, que en el caso de Bitcoin son las transacciones, sin embargo la firma puede hacer commit (firmar específicamente), a un subconjunto de los datos de la transacción, aunque el comportamiento mas común es la firma completa de la transacción.

La bandera _SIGHASH_ es un único byte que es añadido al final de la firma, y esta bandera puede variar con cada entrada (input) de la transacción.

La siguiente tabla muestra los valores que pueden elegirse para el _SIGHASH_:

| Bandera SIGHASH 	| Valor 	| Descripción                                                                                                  	|
|-----------------	|-------	|--------------------------------------------------------------------------------------------------------------	|
| ALL             	| 0x01  	| La firma hace commit a todas las entradas y todas las salidas                                                	|
| NONE            	| 0x02  	| La firma hace commit a todas las entradas y ninguna de las salidas                                           	|
| SINGLE          	| 0x03  	| La firma hace commit a todas las entradas pero solo a la salida<br>con el mismo número de input que se firma 	|

Adicionalmente esxiste un modificador llamado _SIGHASH_ANYONECANPAY_ que puede comnbinarse con los valores que ya vimos. Con _ANYONECANPAY_ solo el un input es firmado, por lo que cualquier persona puede añadir inputs adicionales, probablemente de allí su nombre (CUALQUIERA PUEDE PAGAR).

El modificador tiene un valor de _0x80_ y se aplica con un modificador de bit OR al valor del _SIGHASH_, veamos como afecta el modificador.

| Bandera SIGHASH 	| ANYONECANPAY 	| Valor 	| Descripción                                                                                         	|
|-----------------	|--------------	|-------	|-----------------------------------------------------------------------------------------------------	|
| ALL             	| ANYONECANPAY 	| 0x81  	| La firma hace commit a una entrada y todas las salidas                                              	|
| NONE            	| ANYONECANPAY 	| 0x82  	| La firma hace commit a una entrada y ninguna de las salidas                                         	|
| SINGLE          	| ANYONECANPAY 	| 0x83  	| La firma hace commit a una entrada, y solo a la salida<br>con el mismo número de input que se firma 	|

es importante notar que las transacciones pueden contener entradas (inputs) de distintos dueños. 

## Casos de uso

### SIGHASH = _ALL_

El caso de uso mas simple es como cualquier transacción de bitcoin que hacemos a través de una cartera, en donde no queremos que las entradas ni las salidas se puedan modificar, en este caso _ALL_ significa que todas las entradas y todas las salidas estan firmadas, por lo que no se podría modifcar la transacción.

### SIGHASH = _ALL_ + _ANYONECANPAY_
En este caso solo una esntrada y todas las salidas serán firmadas, en un caso hipotético en el que tengo una salida mayor a una entrada, alguien mas podria añadir una nueva entrada para completar la transacción.


### SIGHASH = _NONE_
Esta transacción en dode se firman todas las entradas pero no las salidas, equivaldría a firmar un cheque en blanco, cualquiera puede modificar la transacción modificando las salidas existentes o creando otras

### SIGHASH = _NONE_ + _ANYONECANPAY_
Esta construcción puede ser utilizada como un collector de "dust" (UTXOs de montos muy pequeños) en donde estos UTXOs normalmente ni=o pueden ser gastados porque su tarifa para realizar la transacción excede el valor del "dust" UTXO. En este tipo de transaccion el UTXO puede ser donado para que alguien lo agregue a otros UTXOs para gastarlo.

### SIGHASH = _SIGLE_
Aqui se podría construir una transacción en la que un padre tiene 20 bitcoins y decide enviar 10 a uno de sus hijos y deja que los 10 bitcoins restantes se los distribuyan entre los dos hijos restantes que deberían crear una salida para cada uno.

### SIGHASH = _SINGLE_ + _ANYONECANPAY_
Se firma la entrada y la salida corrrespondiente, el resto de las entradas o salidas se excluyen. esto permite a cualquiera agregar mas entradas y mas salidas. Un caso de uso podría ser la rifa de entradas de 1BTC, en dode la unica que queda firmada es la entrada de 1BTC y la salida de 1BTC. Después de esto cualquiera podrdía agregar una nueva entrada de 1BTC y crear una salida para una persona random, también de 1BTC.
