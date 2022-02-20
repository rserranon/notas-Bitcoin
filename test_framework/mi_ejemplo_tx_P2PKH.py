#!/usr/bin/env python3
# Copyright (c) 2017-2019 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Un ejemplo de como crear transacciones, firmarlas y publicarlas
utilizando el framework funcional.
Trabajo en proceso, sin garantía de funcionar, sigo aprendiendo de Bitcoin y
del framework.
"""
# Imports en orden PEP8 std library primero, después de terceros y 
# finalmente locales


# Evitar importaciones wildcard *
from test_framework.blocktools import COINBASE_MATURITY
from test_framework.messages import CTransaction, CTxIn, CTxOut, COutPoint, COIN
from test_framework.script_util import keyhash_to_p2pkh_script

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal
from test_framework.address import hash160, byte_to_base58

# Mi clase de prueba hereda de BitcoinTestFramework
class ExampleTest(BitcoinTestFramework):

    def set_test_params(self):
        """Este método debe ser sobrescrito para setear los parámetros de la
        prueba."""
        # Cadena nueva, 1 solo nodo de bitcoind y no hay parámetros en la línea de
        # comandos para el nodo
        self.setup_clean_chain = True
        self.num_nodes = 1
        self.extra_args = [[]]

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()


    def run_test(self):
        """Main test logic"""
        self.log.info("Prueba iniciando!")
        self.log.info("Crear algunos bloques 101 y hacer que madure el bloque1")        
        blocks = self.generate(self.nodes[0], COINBASE_MATURITY + 1)

        # Después de generar 101 bloques  hay un UTXO del bloque 1 por 50BTC
        utxos = self.nodes[0].listunspent()
        assert len(utxos) == 1
        assert_equal(utxos[0]["amount"], 50) 

        self.log.info("Seleccionar el UTXO que buscamos")
        utxo = utxos[0]
        self.log.info("UTXOs selecionado: {}".format(utxo))


        address = self.nodes[0].getnewaddress()
        pubkey = self.nodes[0].getaddressinfo(address)['pubkey']
        pubkey_hash = hash160(pubkey.encode()) # .encode() se requiere para convertir a bytes
        script_pubkey = keyhash_to_p2pkh_script(pubkey_hash) 
        # Nuestro Script en un Pay to Public to Key Hash
        # OP_DUP OP_HASH160 <pubkey_hash> OP_EQUALVERIFY OP_CHECKSIG
        self.log.info("P2SH Script: {}".format(repr(script_pubkey)))
        # 111 = version bytes de testnet para la conversion a base 58
        # fuente: https://en.bitcoin.it/wiki/Base58Check_encoding#Encoding_a_Bitcoin_address
        destination_address = byte_to_base58(pubkey_hash, 111) 
        # La dirección de destino es el pubkey_hash del pubkey en base58    
        self.log.info("Destination address: {}".format(destination_address))

        self.log.info("Crear la transacción")
        self.relayfee = self.nodes[0].getnetworkinfo()["relayfee"]
        # COIN = 100,000,000 de sats por BTC
        value = int((utxo["amount"] - self.relayfee) * COIN)
        # Crear la transacción, las entradas y las salidas con ayuda de las
        # clases primitivs de message.py
        tx = CTransaction()
        tx.vin = [CTxIn(COutPoint(int(utxo["txid"], 16), utxo["vout"]))]
        tx.vout = [CTxOut(value, script_pubkey)]
        tx.rehash() # hacer el hasing de la Tx
        self.log.info("Transacción: {}".format(tx))

        self.log.info("Firmar la transacción")
        tx_hex = self.nodes[0].signrawtransactionwithwallet(tx.serialize().hex())["hex"]
        self.log.info("Transacción HEX: {}".format(tx_hex))

        decrawtx = self.nodes[0].decoderawtransaction(tx_hex, True)
        descriptor = decrawtx['vout'][0]['scriptPubKey']['desc']
        # Guardemos el descriptor para buscar mas adelante en el UTXO set
        self.log.info("descriptor: {}".format(descriptor))
        self.log.info("Transacción Decodificada: {}".format(decrawtx))

        # Enviar la transacción al nodo para ser incuida en el mempool
        txid = self.nodes[0].sendrawtransaction(tx_hex)
        self.log.info("Id de Transacción: {}".format(txid))
        
        mempool = self.nodes[0].getrawmempool()
        # asegurar que nuestra transacción está en el mempool
        assert_equal(mempool[0], txid)

        self.log.info("Generar un bloque para que se procese nuestra transacción")        
        blocks = self.generate(self.nodes[0], 1)
        
        # Asegurar que nuestra transacción se minó
        mempool = self.nodes[0].getrawmempool()
        assert len(mempool) == 0

        # Verificar que nuestra transacción movió los BTC a la dirección
        # de destino
        transactions = self.nodes[0].listtransactions()
        assert_equal(transactions[8]["address"], destination_address)
        # self.nodes[0].importaddress(destination_address)




        # TODO entender porque nuestra transacción no aparece en los UTXOs 
        # de esta wallet
        utxos = self.nodes[0].listunspent(minconf=0)
        assert len(utxos) > 0
        self.log.info("UTXOs disponibles: {}".format(utxos))
        # Sin embargo si aparece al escanear el UTXOs set usando el descriptor
        utxo_esperado = self.nodes[0].scantxoutset(action="start", scanobjects=[{'desc': descriptor}])

if __name__ == '__main__':
    ExampleTest().main()