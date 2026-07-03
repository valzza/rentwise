import { useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Spinner from "../../components/ui/Spinner";
import toast from "react-hot-toast";

export default function Profile() {
    const setUser = useAuthStore((s) => s.setUser);
    const [profile, setProfile] = useState(null);
    const [form, setForm] = useState({ first_name: "", last_name: "" });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        authApi.getMe().then(({ data }) => {
            setProfile(data);
            setForm({ first_name: data.first_name, last_name: data.last_name });
        });
    }, []);

    const save = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            const { data } = await authApi.updateMe(form);
            setProfile(data);
            setUser(data);
            toast.success("Profile updated");
        } catch {
            toast.error("Update failed");
        } finally {
            setSaving(false);
        }
    };

    if (!profile) {
        return <DashboardLayout><div className="flex justify-center py-12"><Spinner size="lg" /></div></DashboardLayout>;
    }

    return (
        <DashboardLayout>
            <h1 className="text-xl font-semibold text-gray-900 mb-6">My Profile</h1>
            <div className="max-w-lg space-y-6">
                <form onSubmit={save} className="rounded-xl border bg-white p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                        <Input label="First name" value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} required />
                        <Input label="Last name" value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} required />
                    </div>
                    <Input label="Email" value={profile.email} disabled />
                    <div className="flex flex-wrap gap-2">
                        {profile.roles?.map((r) => (
                            <span key={r} className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 ring-1 ring-brand-100">{r}</span>
                        ))}
                    </div>
                    <Button type="submit" loading={saving}>Save changes</Button>
                </form>
                <p className="text-xs text-gray-400">Member since {new Date(profile.created_at).toLocaleDateString()}.</p>
            </div>
        </DashboardLayout>
    );
}