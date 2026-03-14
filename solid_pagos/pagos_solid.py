"""
pagos_solid.py - Sistema de Pagos con Principios SOLID
Autor: Andrik27
Fecha: 14/03/2026

Aplicación de principios:
- SRP: Cada clase tiene una única responsabilidad
- OCP: Fácil agregar nuevos métodos de pago
- LSP: Todos los métodos son intercambiables
- ISP: Interfaz pequeña y específica
- DIP: PaymentProcessor depende de abstracción PaymentMethod
"""

from abc import ABC, abstractmethod
from datetime import datetime

# ==================== PASO 1: INTERFAZ (CONTRATO) ====================
class PaymentMethod(ABC):
    """Interfaz que define el contrato para todos los métodos de pago"""
    
    @abstractmethod
    def process_payment(self, amount: float, currency: str) -> dict:
        """Procesa un pago con el monto y moneda especificados"""
        pass
    
    @abstractmethod
    def validate(self, amount: float) -> bool:
        """Valida si el pago puede procesarse"""
        pass

# ==================== PASO 2: IMPLEMENTACIONES CONCRETAS ====================

class PayPalPayment(PaymentMethod):
    """Implementación para pagos con PayPal - Responsabilidad Única"""
    
    def __init__(self, email: str):
        self.email = email
        self.fee_percentage = 0.035  # 3.5% de comisión
    
    def process_payment(self, amount: float, currency: str = "USD") -> dict:
        if not self.validate(amount):
            raise ValueError(f"Monto ${amount} excede el límite permitido para PayPal")
        
        # Calcular comisión
        fee = round(amount * self.fee_percentage, 2)
        net_amount = round(amount - fee, 2)
        
        # Generar transacción
        transaction = {
            "method": "PayPal",
            "account": self.email,
            "amount": amount,
            "currency": currency,
            "fee": fee,
            "net_amount": net_amount,
            "status": "COMPLETED",
            "transaction_id": f"PAYPAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"  📧 PayPal: ${amount} (Comisión: ${fee})")
        return transaction
    
    def validate(self, amount: float) -> bool:
        return 0 < amount <= 5000  # Límite de $5000 para PayPal


class StripePayment(PaymentMethod):
    """Implementación para pagos con Stripe - Responsabilidad Única"""
    
    def __init__(self, api_key: str, card_last_four: str):
        self.api_key = api_key
        self.card_last_four = card_last_four
        self.fee_percentage = 0.029  # 2.9%
        self.fixed_fee = 0.30  # $0.30 por transacción
    
    def process_payment(self, amount: float, currency: str = "USD") -> dict:
        if not self.validate(amount):
            raise ValueError("Monto inválido para Stripe")
        
        # Calcular comisión
        fee = round((amount * self.fee_percentage) + self.fixed_fee, 2)
        net_amount = round(amount - fee, 2)
        
        # Generar transacción
        transaction = {
            "method": "Stripe",
            "card_last_four": self.card_last_four,
            "amount": amount,
            "currency": currency,
            "fee": fee,
            "net_amount": net_amount,
            "status": "COMPLETED",
            "transaction_id": f"STRIPE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"  💳 Stripe: ${amount} (Comisión: ${fee})")
        return transaction
    
    def validate(self, amount: float) -> bool:
        return amount > 0


class CryptoPayment(PaymentMethod):
    """Implementación adicional para demostrar OCP - Fácil de agregar sin modificar código existente"""
    
    def __init__(self, wallet_address: str, crypto_type: str = "BTC"):
        self.wallet_address = wallet_address
        self.crypto_type = crypto_type
        self.fee_percentage = 0.001  # 0.1%
    
    def process_payment(self, amount: float, currency: str = "BTC") -> dict:
        if not self.validate(amount):
            raise ValueError("Monto inválido para Crypto")
        
        fee = round(amount * self.fee_percentage, 8)
        net_amount = round(amount - fee, 8)
        
        transaction = {
            "method": f"Crypto ({self.crypto_type})",
            "wallet": self.wallet_address[:8] + "...",
            "amount": amount,
            "currency": currency,
            "fee": fee,
            "net_amount": net_amount,
            "status": "COMPLETED",
            "transaction_id": f"CRYPTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"  🪙 Crypto: ${amount} (Comisión: {fee})")
        return transaction
    
    def validate(self, amount: float) -> bool:
        return amount > 0


# ==================== PASO 3: CLASE DE ALTO NIVEL ====================

class PaymentProcessor:
    """
    Clase de alto nivel que procesa pagos
    DIP: Depende de la abstracción PaymentMethod, no de implementaciones concretas
    SRP: Única responsabilidad = procesar pagos y mantener historial
    """
    
    def __init__(self, payment_method: PaymentMethod = None):
        """Inyección de dependencia - Recibe cualquier método que implemente PaymentMethod"""
        self.payment_method = payment_method
        self.transactions = []
        self.processed_count = 0
    
    def process(self, amount: float, currency: str = "USD", description: str = "") -> dict:
        """Procesa un pago usando el método inyectado"""
        if not self.payment_method:
            raise ValueError("No hay método de pago configurado")
        
        print(f"\n▶️ Procesando: {description}")
        print(f"   Monto: {currency} {amount}")
        
        try:
            # Delegar el procesamiento al método específico
            transaction = self.payment_method.process_payment(amount, currency)
            transaction["description"] = description
            transaction["processor"] = "PaymentProcessor v1.0"
            
            # Guardar en historial
            self.transactions.append(transaction)
            self.processed_count += 1
            
            print(f"   ✅ Pago exitoso - ID: {transaction['transaction_id']}")
            return transaction
            
        except Exception as e:
            error_transaction = {
                "status": "FAILED",
                "error": str(e),
                "amount": amount,
                "currency": currency,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            self.transactions.append(error_transaction)
            print(f"   ❌ Error: {e}")
            return error_transaction
    
    def set_payment_method(self, new_method: PaymentMethod):
        """Cambia el método de pago en tiempo de ejecución"""
        old_method = type(self.payment_method).__name__ if self.payment_method else "None"
        self.payment_method = new_method
        print(f"🔄 Método cambiado: {old_method} → {type(new_method).__name__}")
    
    def get_statistics(self) -> dict:
        """Retorna estadísticas de procesamiento"""
        completed = [t for t in self.transactions if t.get("status") == "COMPLETED"]
        failed = [t for t in self.transactions if t.get("status") == "FAILED"]
        
        total_amount = sum(t.get("amount", 0) for t in completed)
        total_fees = sum(t.get("fee", 0) for t in completed)
        
        return {
            "total_transactions": len(self.transactions),
            "completed": len(completed),
            "failed": len(failed),
            "total_amount": total_amount,
            "total_fees": total_fees,
            "net_amount": total_amount - total_fees
        }
    
    def show_history(self):
        """Muestra el historial de transacciones"""
        print("\n" + "="*60)
        print("📊 HISTORIAL DE TRANSACCIONES")
        print("="*60)
        
        for i, t in enumerate(self.transactions, 1):
            if t.get("status") == "COMPLETED":
                print(f"{i}. {t['method']}: {t['currency']} {t['amount']} - {t['status']} - {t.get('description', '')}")
            else:
                print(f"{i}. ❌ FALLIDO: {t.get('error')} - {t.get('description', '')}")


# ==================== DEMOSTRACIÓN PRÁCTICA ====================

def demostrar_srp():
    """Demostración de Responsabilidad Única"""
    print("\n📌 DEMOSTRACIÓN SRP: Cada clase tiene una responsabilidad")
    print("-"*50)
    print("PayPalPayment: Solo procesa pagos PayPal")
    print("StripePayment: Solo procesa pagos Stripe")
    print("CryptoPayment: Solo procesa pagos Crypto")
    print("PaymentProcessor: Solo coordina el procesamiento")

def demostrar_ocp():
    """Demostración de Abierto/Cerrado"""
    print("\n📌 DEMOSTRACIÓN OCP: Abierto para extensión, cerrado para modificación")
    print("-"*50)
    print("Podemos agregar nuevos métodos (ApplePay, Transferencia, etc.)")
    print("sin modificar el código existente de PaymentProcessor")

def demostrar_lsp():
    """Demostración de Sustitución de Liskov"""
    print("\n📌 DEMOSTRACIÓN LSP: Todos los métodos son intercambiables")
    print("-"*50)
    print("PayPal, Stripe y Crypto pueden usarse indistintamente")
    print("en PaymentProcessor sin problemas")

def demostrar_isp():
    """Demostración de Segregación de Interfaces"""
    print("\n📌 DEMOSTRACIÓN ISP: Interfaz pequeña y específica")
    print("-"*50)
    print("PaymentMethod solo tiene 2 métodos:")
    print("- process_payment(): Para procesar pagos")
    print("- validate(): Para validar montos")

def demostrar_dip():
    """Demostración de Inversión de Dependencias"""
    print("\n📌 DEMOSTRACIÓN DIP: Dependencia de abstracciones")
    print("-"*50)
    print("PaymentProcessor depende de la interfaz PaymentMethod")
    print("No depende de PayPal, Stripe o Crypto directamente")


# ==================== EJECUCIÓN PRINCIPAL ====================

if __name__ == "__main__":
    print("="*60)
    print("🚀 SISTEMA DE PROCESAMIENTO DE PAGOS SOLID")
    print("="*60)
    print("Estudiante: Andrik27")
    print("Fecha: 14/03/2026")
    print("="*60)
    
    # Demostración teórica de los principios
    print("\n📚 VERIFICACIÓN DE PRINCIPIOS SOLID")
    print("="*60)
    demostrar_srp()
    demostrar_ocp()
    demostrar_lsp()
    demostrar_isp()
    demostrar_dip()
    
    # Crear métodos de pago
    print("\n🛠️ Creando métodos de pago...")
    paypal = PayPalPayment("andrik27@email.com")
    stripe = StripePayment("sk_live_123456789", "4242")
    crypto = CryptoPayment("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "BTC")
    
    # Crear procesador sin método inicial (para demostrar flexibilidad)
    processor = PaymentProcessor()
    
    # ESCENARIO 1: Pago con PayPal
    print("\n" + "="*60)
    print("ESCENARIO 1: Pago con PayPal")
    print("="*60)
    processor.set_payment_method(paypal)
    processor.process(150.00, "USD", "Curso de Python")
    processor.process(299.99, "USD", "Certificación SOLID")
    
    # ESCENARIO 2: Pago con Stripe
    print("\n" + "="*60)
    print("ESCENARIO 2: Pago con Stripe")
    print("="*60)
    processor.set_payment_method(stripe)
    processor.process(89.99, "USD", "Suscripción mensual")
    processor.process(499.99, "USD", "Laptop nueva")
    
    # ESCENARIO 3: Pago con Crypto
    print("\n" + "="*60)
    print("ESCENARIO 3: Pago con Crypto (Demostrando OCP)")
    print("="*60)
    processor.set_payment_method(crypto)
    processor.process(0.05, "BTC", "Compra de NFT")
    
    # ESCENARIO 4: Prueba de validación
    print("\n" + "="*60)
    print("ESCENARIO 4: Prueba de validación")
    print("="*60)
    processor.set_payment_method(paypal)
    processor.process(10000.00, "USD", "Intento de pago grande - Debe fallar")
    
    # Mostrar historial completo
    processor.show_history()
    
    # Mostrar estadísticas
    print("\n" + "="*60)
    print("📈 ESTADÍSTICAS DEL PROCESADOR")
    print("="*60)
    stats = processor.get_statistics()
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Resumen de principios aplicados
    print("\n" + "="*60)
    print("✅ PRINCIPIOS SOLID APLICADOS CORRECTAMENTE")
    print("="*60)
    print("""
    📌 SRP: 
       - PayPalPayment: Solo procesa PayPal
       - StripePayment: Solo procesa Stripe
       - CryptoPayment: Solo procesa Crypto
       - PaymentProcessor: Solo coordina pagos
    
    📌 OCP: 
       - Podemos agregar ApplePay, Transferencia, etc.
       - Sin modificar PaymentProcessor
    
    📌 LSP: 
       - Todos los métodos heredan de PaymentMethod
       - Cualquiera puede reemplazar a otro
    
    📌 ISP: 
       - Interfaz con solo 2 métodos necesarios
       - Sin métodos forzados innecesarios
    
    📌 DIP: 
       - PaymentProcessor depende de abstracción
       - No depende de implementaciones concretas
    """)
    
    print("="*60)
    print("🎉 PROGRAMA COMPLETADO EXITOSAMENTE")
    print("="*60)