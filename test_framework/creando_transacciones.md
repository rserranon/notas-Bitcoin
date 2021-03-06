# Crear transacciones

Lo primero a comentar, es que es muy importante entender como funcionan las transacciones en Bitcoin antes de pretender crear transacciones. Para ello, te recomiendo el libro de Mastering Bitcoin de Andreas Antonopoulos. Esta sección la iremos complementando conforme yo mismo pueda hacer mas pruebas con cada tipo de transacción. Por lo pronto empezaremos con algunas de ellas.

En esta tabla podemos ver todos los tipos de salidas (outputs) que se pueden generar, iremos completando poco a poco los ejemplos para cubrir toda la tabla.

| vout               	| scriptPubKey                                                        	| scriptSig                   	| redeem<br>script 	| witness                                	|
|--------------------	|---------------------------------------------------------------------	|-----------------------------	|------------------	|----------------------------------------	|
| P2PK               	| pubKey<br>OP_CHECKSIG                                           	| signature                   	|                  	|                                        	|
| P2PKH              	| OP_DUP<br>OP_HASH160<br>pubKeyHash<br>OP_EQUALVERIFY<br>OP_CHECKSIG 	| signature<br>public key     	|                  	|                                        	|
| P2SH               	| OP_HASH160<br>scriptHash<br>OP_EQUAL                                	| data pushes<br>redem script 	| arbitrary        	|                                        	|
| P2WPKH             	| 0<br>pubKeyHash                                                     	|                             	|                  	| signature<br>public key                	|
| P2WSH              	| 0<br>witnessScriptHash                                              	|                             	|                  	| data pushes<br>witness script          	|
| P2WSH P2WPKH       	| OP_HASH160<br>redemScriptHash<br>OP_EQUAL                           	| redem script                	| 0<br>pubKeyHash  	| signature<br>public key                	|
| P2SH P2WSH         	| OP_HASH160<br>redemScriptHash                                       	| redem script                	| 0<br>script hash 	| data pushes<br>witness script          	|
| P2TR (key path)    	| 1<br>public key                                                     	|                             	|                  	| signature                              	|
| P2TR (script path) 	| 1<br>public key                                                     	|                             	|                  	| data pushes<br>script<br>control block 	|


## P2PKH Pago a un Hash de una Llave Pública (Pay to Public Key Hash)

Para hacer el pago a un hash de una llave pública, primero tenemos que obtener una llave pública usando el framework, hay varias formas de hacerlo, pero en este caso lo voy a hacer a través de generar una dirección en mi billetera.

```python
    address = self.nodes[0].getnewaddress()
    pubkey = self.nodes[0].getaddressinfo(address)['pubkey']
```

A continuación, lo que requerimos es el hash de la llave pública. Y aprovechamos para usar una función de ayuda que nos crea el scriptPubKey, Script de Cierre, (Locking Script) que utilizaremos en la transacción.

```python
    pubkey_hash = hash160(pubkey.encode()) # es necesario convertir a bytes
    script_pubkey = keyhash_to_p2pkh_script(pubkey_hash)
```

Como la transacción va dirigida a una dirección Bitcoin en particular, la generamos con la función base58 del hash que acabamos de crear, **esta es la dirección Bitcoin a la que irán dirigidos nuestros fondos** en la transacción. Es importante notar que como la codificación es para la red de _regtest_ y para un hash de lláve pública, es necesario utilizar el número 111 como la versión de bytes, como un parámetro de la función. [Aquí lo puedes consultar](https://en.bitcoin.it/wiki/Base58Check_encoding#Encoding_a_Bitcoin_address)

```python
    destination_address = byte_to_base58(pubkey_hash, 111)
```
Primero generemos un bloque maduro (101 confirmaciones, COINBASE_MATURITY + 1) que nos pague la recompensa del Coinbase y seleccionamos el UTXO disponible.

```python
    blocks = self.generate(self.nodes[0], COINBASE_MATURITY + 1)
    # Después de generar 101 bloques,  hay un UTXO del bloque 1 por 50BTC
    utxos = self.nodes[0].listunspent()
    utxo = utxos[0]
```

Ahora si podemos empezar a crear la transacción. Primero, calculemos el monto total a enviar después de restarle el fee mínimo que soporta el nodo. Recordemos que los montos de las transacciones siempre se denominan en satoshis, por eso multiplicamos por COIN (que es igual a 100,000,000 de satoshis por cada BTC).

```python
    self.relayfee = self.nodes[0].getnetworkinfo()["relayfee"]
    # COIN = 100,000,000 de sats por BTC
    value = int((utxo["amount"] - self.relayfee) * COIN)
```

Para crear la transacción utilizaremos las clases primitivas que se encuentran en el archivo `messages.py`: _Ctransaction_, _CoutPoint_, _CTxIn_ y _CTxOut_.

```python
    tx = CTransaction()
    tx.vin = [CTxIn(COutPoint(int(utxo["txid"], 16), utxo["vout"]))]
    tx.vout = [CTxOut(value, script_pubkey)]
    tx.rehash() # hacer el hasing de la Tx
```
Firmemos y enviemos la transacción. Y para que se procese, minemos un bloque.

```python
    tx_hex = self.nodes[0].signrawtransactionwithwallet(tx.serialize().hex())["hex"]
    txid = self.nodes[0].sendrawtransaction(tx_hex)
    blocks = self.generate(self.nodes[0], 1)
```

Nuestra transacción ya ha sido añadida al mempool y posteriormente minada al generar un bloque.

En el siguiente link puedes encontrar [el caso completo de prueba](mi_ejemplo_tx_P2PKH.py) con algunas instrucciones adicionales, para validar que todos los pasos de la creación y minado de la transacción han sido exitosos. Para poder correr el ejemplo, lo tienes que copiar al directorio `test/functional` de Bitcoin Core, para que pueda tener acceso a las librerías del framework.

## P2PK Pago a una llave pública (Pay to Public Key)

Primero es importante aclarar que los pagos a llaves públicas han sido deprecados en favor de pagos P2PKH. 

Sin embargo aquí veremos como se generan. Empezamos generando una llave privada y con ella una llave pública.

```python
    key = ECKey()
    key.generate()
    pubkey = key.get_pubkey()
```
Usamos una función de ayuda que nos crea el scriptPubKey, Script de Cierre, (Locking Script) que utilizaremos en la transacción.

```python
    script_pubkey = key_to_p2pk_script(pubkey.get_bytes())
    self.log.info("P2SH Script: {}".format(repr(script_pubkey)))
```
El resto del proceso es similar al del P2PKH, sin embargo un tema que tenemos que analizar a fondo y quedará como pendiente (TODO) es porque la transacción en la lista de UTXOs tiene una dirección de destino que no pudimos generar al inicio. Averiguaremos si tiene que ver con el proceso de deprecación en favor de pagos P2PKH.

En el siguiente link puedes encontrar [el caso completo de prueba](mi_ejemplo_tx_P2PK.py) con algunas instrucciones adicionales y comentarios, para validar que todos los pasos de la creación y minado de la transacción han sido exitosos. Para poder correr el ejemplo, lo tienes que copiar al directorio `test/functional` de Bitcoin Core, para que pueda tener acceso a las librerías del framework.

## P2SH Pago a un Hash de un Script (Pay to Script Hash)

El proceso para crear una transacción P2SH es bastante similar, la principal diferencia es que, en lugar de obtener la dirección de destino de los bitcoins, a través del hash de una llave pública, lo hacemos con el hash de un script. **Esta dirección es a la que irán destinados nuestros fondos**.También es importante notar que la conversión a base58 para obtener la dirección utiliza un código de versión de bytes distinto para _regtest_ y para el _hash_ del script que es igual a _196_. La referencia completa de [como utilizar los bytes de versión la puedes consultar aquí](https://en.bitcoin.it/wiki/Base58Check_encoding#Encoding_a_Bitcoin_address).

En esta sección de código puedes ver como se realiza la construcción del Script, el hashing, la conversión a base58 para obtener la dirección Bitcoin de destino y el armado del scriptPubKey (Script de Cierre).

```python
        script = CScript([OP_TRUE])
        script_hash = hash160(script)
        destination_address = byte_to_base58(script_hash, 196) # 196, Bitcoin testnet script hash
        self.log.info("Destination Address: {}".format(destination_address))
        script_pubkey = scripthash_to_p2sh_script(script_hash)
```

En el siguiente link puedes encontrar [el caso completo de prueba](mi_ejemplo_tx_P2SH.py) con algunas instrucciones adicionales y comentarios, para validar que todos los pasos de la creación y minado de la transacción han sido exitosos. Para poder correr el ejemplo, lo tienes que copiar al directorio `test/functional` de Bitcoin Core, para que pueda tener acceso a las librerías del framework.

## MultiSig, Envío a una dirección multifirma

Para el caso de envío a una dirección multifirma utilizaremos 3 nodos para crear distintas llaves públicas.

```python
node0, node1, node2 = self.nodes
    publicK0 = node0.getaddressinfo(node0.getnewaddress())['pubkey']
    publicK1 = node1.getaddressinfo(node1.getnewaddress())['pubkey']
    publicK2 = node2.getaddressinfo(node2.getnewaddress())['pubkey']
    keys=[publicK0, publicK1, publicK2]
```
Una vez que tenemos las llaves en la lista `keys` procedemos a crear la multifirma. Aprovechamos también para guardar la dirección de destino y el descriptor que nos servirá para obtener la dirección de la transacción y del UTXO mas adelante y verificar que coincide con la de destino, **aqui es a donde se tranferiran nuestros fondos de Bitcoin.**

```python
    multi_sig = node0.createmultisig(2, keys, 'legacy')
    destination_addr = multi_sig['address']
    descriptor = multi_sig['descriptor']
```
Finalmente hacemos el envío de la transacción a la dirección de destino.

```python
    txid = node0.sendtoaddress(destination_addr, 40)
```

En el siguiente link puedes encontrar [el caso completo de prueba](mi_ejemplo_tx_MultiSig.py) con algunas instrucciones adicionales y comentarios, para validar que todos los pasos de la creación y minado de la transacción han sido exitosos. Para poder correr el ejemplo, lo tienes que copiar al directorio `test/functional` de Bitcoin Core, para que pueda tener acceso a las librerías del framework.

## P2TR, Pago a Taproot (Pay to Taproot)

El caso de Pago a Taprrot requiere iniciar el nodo con los siguientes argumentos:

```python
        self.setup_clean_chain = True
        self.num_nodes = 1
        self.extra_args = [["-vbparams=taproot:1:1", "-addresstype=bech32m", "-changetype=bech32m"]]
```
Lo primero que hay que hacer es crear una nueva billetera que funcione con descriptores:

```python
        self.nodes[0].createwallet(wallet_name="TapRoot", descriptors=True, blank=True)
```

Creamos nuestra semilla, y XPRIV utilizando esta [página para crear semillas BIP39.](https://iancoleman.io/bip39/)

Importamos el XPRIV y definimos la ruta de derivación (derivation path) de Taproot:

```python
    xpriv = 'tprv8ZgxMBicQKsPf2h5QMyUYcsbeu8jfz6tR7a7jJpvhBaPJsddMfZdYdhH7mrXPve58KTicWsrJPGEC1XSkHMhHoMxyUuauDWVtvAFvQFNsrM'
    derivation_path = "/86'/1'/0'/0/*"
```

Generamos el descriptor y el decriptor que incluye el chechsum:

```python
        descriptor = f"tr({xpriv}{derivation_path})"
        descriptor_checksum = descsum_create(descriptor)
```
Importamos el descriptor:
```python
        res = self.nodes[0].importdescriptors([
            {
                "desc": descriptor_checksum,
                "active": True,
                "timestamp": "now"
            }])
```

Una vez que generamos suficientes bloques para tener UTXOs disponibles, seleccionamos un UTXO y generamos la dirección de destino, creamos la transacción, la firmamos y la enviamos al mempool para ser procesada:

```python
        destination_address = self.nodes[0].getnewaddress(address_type='bech32m')

        tx = self.nodes[0].createrawtransaction([{"txid": utxo["txid"], "vout": utxo["vout"]}], {destination_address: 49.999})
        signed_tx = self.nodes[0].signrawtransactionwithwallet(tx)['hex']
        txid = self.nodes[0].sendrawtransaction(signed_tx)
```

En el siguiente link puedes encontrar [el caso completo de prueba](mi_ejemplo_tx_P2TR.py) con algunas instrucciones adicionales y comentarios, para validar que todos los pasos de la creación y minado de la transacción han sido exitosos. Para poder correr el ejemplo, lo tienes que copiar al directorio `test/functional` de Bitcoin Core, para que pueda tener acceso a las librerías del framework.

Espero que esto te haya ayudado a animarte a usar el framework para crear transacciones y nuevos casos de prueba.

Conforme vaya creando casos nuevos iré actualizando esta guía, si te interesa ayudar o hacer algún comentario puedes mandarme un mensaje por twitter a [@Bitcoin_1o1](https://twitter.com/bitcoin_1o1).