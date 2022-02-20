# Crear transacciones

Lo primero a comentar es que es muy importante entender como funcionan las transacciones en Bitcoin antes de pretender crear transacciones. Para ello te recomiendo el libro de Mastering Bitcoin de Andreas Antonopoulos. Esta seccion la iremos complementando conforme yo mismo pueda hacer mas pruebas con cada tipo de transacción. Por lo pronto empezaremos con una de ellas.

## P2PKH Pago a un Hash de una Llave Pública (Pay to Public Key Hash)

Para hacer el pago a un hash de una lláve pública primero tenemos que obetener una llave pública usando el framework, hay varias formas de hacerlo pero en este caso lo voy a hacer a través de generar una dirección en mi billetera.

```python
    address = self.nodes[0].getnewaddress()
    pubkey = self.nodes[0].getaddressinfo(address)['pubkey']
```

A continuación lo que requerimos es el hash de la llave pública. Y aprovechamos para usar una función de ayuda que nos crea el scriptPubKey,Script de Cierre, (Locking Script) que utilizaremos en la transacción.

```python
    pubkey_hash = hash160(pubkey.encode()) # es necesario convertir a bytes
    script_pubkey = keyhash_to_p2pkh_script(pubkey_hash)
```

Como la transacción va dirigida a una dirección Bitcoin en particular, la generamos con la funcion base58 del hash que acabamos de crear, esta es la dirección Bitcoin a la que irán dirigidos nuestros fondos en la transacción. Es importante notar que como la codificación es para la red de _regtest_, es necesario utilizar el número 111 como la versión de bytes, como un parámertro de la función. [Aquí lo puedes consultar](https://en.bitcoin.it/wiki/Base58Check_encoding#Encoding_a_Bitcoin_address)

```python
    destination_address = byte_to_base58(pubkey_hash, 111)
```
Primero generemos un bloque maduro(101 confirmaciones, COINBASE_MATURITY + 1) que nos pague la recompaensa del Coinbase y seleccionesmos el UTXO disponible.

```python
    blocks = self.generate(self.nodes[0], COINBASE_MATURITY + 1)
    # Después de generar 101 bloques  hay un UTXO del bloque 1 por 50BTC
    utxos = self.nodes[0].listunspent()
    utxo = utxos[0]
```

Ahora si podemos empezar a crear la transacción. Primero calculemos el monto total a enviar después del fee mínimo que soporta el nodo. Recordemos que los montos de las transaciones siempre se denominan en satoshis, por eso multiplicamos por COIN (que es igual a 100,000,000 de satoshis por cada BTC).

```python
    self.relayfee = self.nodes[0].getnetworkinfo()["relayfee"]
    # COIN = 100,000,000 de sats por BTC
    value = int((utxo["amount"] - self.relayfee) * COIN)
```

Para crear la transaccion utilizaremos las primitivas que se encuentran en el archivo `messages.py`.

```python
    tx = CTransaction()
    tx.vin = [CTxIn(COutPoint(int(utxo["txid"], 16), utxo["vout"]))]
    tx.vout = [CTxOut(value, script_pubkey)]
    tx.rehash() # hacer el hasing de la Tx
```
Firmemos y enviemos la transacción. Y para que se procese minemos un bloque.

```python
    tx_hex = self.nodes[0].signrawtransactionwithwallet(tx.serialize().hex())["hex"]
    txid = self.nodes[0].sendrawtransaction(tx_hex)
    blocks = self.generate(self.nodes[0], 1)
```

Nuestra transaccion ya ha sido añadida al mempool y posteriormente minada al generar un bloque.

En el siguiente link puedes encontrar [el caso completo de prueba con algunas instrucciones adicionales](mi_ejemplo_tx_P2PKH.py), creadas para validar que todos los pasos de la creación y minado de la transacción han sido exitosos. Para poder correr el ejemplo lo tienes que copiar al directorio /src/test/functional de Bitcoin core.

Espero que esto te haya ayudado a animarte a usar el framework para crear transacciones y casos de prueba.

Conforme vaya creando casos nuevos ire actualizando esta guía.
