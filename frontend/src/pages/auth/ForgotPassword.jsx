import { useState } from "react";
import { Link } from "react-router-dom";
import AuthLayout from "../../layouts/AuthLayout";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import toast from "react-hot-toast";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Placeholder — email reset flow not wired to backend yet
    toast.success("If that email exists, a reset link has been sent.");
    setSent(true);
  };

  return (
    <AuthLayout title="Reset your password" subtitle="Enter your email and we'll send a reset link">
      {sent ? (
        <p className="text-center text-sm text-gray-600">
          Check your inbox.{" "}
          <Link to="/login" className="text-brand-600 hover:underline">Back to login</Link>
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Button type="submit" className="w-full">Send reset link</Button>
          <p className="text-center text-sm text-gray-500">
            <Link to="/login" className="text-brand-600 hover:underline">Back to login</Link>
          </p>
        </form>
      )}
    </AuthLayout>
  );
}
