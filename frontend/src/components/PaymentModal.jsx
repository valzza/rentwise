// Lazy-loaded — only imports @stripe/react-stripe-js when payment is triggered
import { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Elements, CardElement, useStripe, useElements } from "@stripe/react-stripe-js";
import { paymentApi } from "../api/paymentApi";
import Button from "./ui/Button";
import toast from "react-hot-toast";

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY ?? "pk_test_placeholder");

function CheckoutForm({ leaseId, amount, onSuccess, onClose }) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);

  const handlePay = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setLoading(true);
    try {
      const { data } = await paymentApi.createIntent(leaseId);
      const result = await stripe.confirmCardPayment(data.client_secret, {
        payment_method: { card: elements.getElement(CardElement) },
      });

      if (result.error) {
        toast.error(result.error.message);
      } else {
        toast.success("Payment successful!");
        onSuccess();
      }
    } catch {
      toast.error("Payment failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handlePay} className="space-y-4">
      <div className="rounded-lg border border-gray-300 bg-white p-3">
        <CardElement options={{ style: { base: { fontSize: "14px" } } }} />
      </div>
      <p className="text-sm text-gray-600">
        You will be charged <strong>${Number(amount).toLocaleString()}</strong> as a deposit.
      </p>
      <div className="flex gap-3">
        <Button type="button" variant="secondary" onClick={onClose} className="flex-1">Cancel</Button>
        <Button type="submit" loading={loading} className="flex-1">Pay ${Number(amount).toLocaleString()}</Button>
      </div>
    </form>
  );
}

export default function PaymentModal({ lease, onSuccess, onClose }) {
  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm
        leaseId={lease.id}
        amount={lease.deposit_amount}
        onSuccess={onSuccess}
        onClose={onClose}
      />
    </Elements>
  );
}
