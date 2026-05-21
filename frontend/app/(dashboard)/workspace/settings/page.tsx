"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/supabaseClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "react-toastify";
import { Loader2, Upload, Bell, Globe, Zap, Shield, Key } from "lucide-react";
import NavHeader from "@/components/NavHeader";

function trialDaysLeft(trialEndDate: string): number {
    try {
        const end = new Date(trialEndDate);
        const now = new Date();
        const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        return Math.max(0, diff);
    } catch {
        return 0;
    }
}

export default function WorkspaceSettingsPage() {
    const { user, setUser, loading: authLoading } = useAuth();
    const router = useRouter();
    const supabase = createClient();

    const [isLoading, setIsLoading] = useState(false);
    const [firstname, setFirstname] = useState("");
    const [lastname, setLastname] = useState("");
    const [avatarFile, setAvatarFile] = useState<File | null>(null);
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    useEffect(() => {
        if (!authLoading && !user) {
            router.push("/login");
        }
        if (user) {
            setFirstname(user.firstname || "");
            setLastname(user.lastname || "");
            setEmail(user.email || "");
            setAvatarPreview(user.avatar_url || null);
        }
    }, [user, authLoading, router]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setAvatarFile(file);
            setAvatarPreview(URL.createObjectURL(file));
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            let avatarUrl = user?.avatar_url;

            // 1. Upload Avatar if changed
            if (avatarFile && user?.userId) {
                const fileExt = avatarFile.name.split('.').pop();
                const filePath = `avatars/${user.userId}-${Math.random()}.${fileExt}`;

                const { error: uploadError } = await supabase.storage
                    .from('avatars')
                    .upload(filePath, avatarFile);

                if (uploadError) {
                    throw uploadError;
                }

                const { data: publicUrlData } = supabase.storage
                    .from('avatars')
                    .getPublicUrl(filePath);

                avatarUrl = publicUrlData.publicUrl;
            }

            // 2. Update User Metadata & Email/Password
            const updates: { email?: string; password?: string; data: { firstname: string; lastname: string; avatar_url?: string | null } } = {
                data: {
                    firstname,
                    lastname,
                    avatar_url: avatarUrl
                }
            };

            if (email !== user?.email) {
                updates.email = email;
            }

            if (password.length > 0) {
                updates.password = password;
            }

            const { data, error } = await supabase.auth.updateUser(updates);

            if (error) throw error;

            // 3. Update Local State via Context
            if (data.user && user) {
                setUser({
                    ...user,
                    firstname: data.user.user_metadata.firstname,
                    lastname: data.user.user_metadata.lastname,
                    avatar_url: data.user.user_metadata.avatar_url,
                    email: data.user.email || user.email
                });
                toast.success("Settings updated successfully!");
                setPassword(""); // Clear password field
            }

        } catch (error: unknown) {
            console.error(error);
            const errorMessage = error instanceof Error ? error.message : "Failed to update settings";
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-black text-white">
                <Loader2 className="w-8 h-8 animate-spin text-green-400" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#06080d] text-white pb-20">
            <NavHeader currentNav="Workspace Settings" />

            <div className="max-w-4xl mx-auto px-4 py-12 space-y-8">
                {/* Profile & Account Card */}
                <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm text-white">
                    <CardHeader>
                        <CardTitle className="text-2xl flex items-center gap-2">
                            <Shield className="w-6 h-6 text-green-400" />
                            Account Profile
                        </CardTitle>
                        <CardDescription className="text-zinc-400">
                            Manage your personal information and login credentials.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSave} className="space-y-8">
                            {/* Avatar Section */}
                            <div className="flex flex-col md:flex-row items-center gap-6 p-4 rounded-xl bg-white/5 border border-white/5">
                                <div className="relative group">
                                    <Avatar className="w-24 h-24 border-2 border-zinc-700">
                                        <AvatarImage src={avatarPreview || ""} className="object-cover" />
                                        <AvatarFallback className="bg-zinc-800 text-2xl font-bold">
                                            {firstname?.[0] || user.email?.[0]?.toUpperCase()}
                                        </AvatarFallback>
                                    </Avatar>
                                    <label htmlFor="avatar-upload" className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                                        <Upload className="w-6 h-6 text-white" />
                                    </label>
                                    <input
                                        id="avatar-upload"
                                        type="file"
                                        accept="image/*"
                                        className="hidden"
                                        onChange={handleFileChange}
                                    />
                                </div>
                                <div className="space-y-1 text-center md:text-left">
                                    <h3 className="font-medium text-lg">Profile Picture</h3>
                                    <p className="text-sm text-zinc-400">
                                        Update your avatar to personalize your workspace.
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <Label htmlFor="firstname">First Name</Label>
                                    <Input
                                        id="firstname"
                                        value={firstname}
                                        onChange={(e) => setFirstname(e.target.value)}
                                        className="bg-black/40 border-zinc-800 focus:border-green-400"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="lastname">Last Name</Label>
                                    <Input
                                        id="lastname"
                                        value={lastname}
                                        onChange={(e) => setLastname(e.target.value)}
                                        className="bg-black/40 border-zinc-800 focus:border-green-400"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email Address</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="bg-black/40 border-zinc-800 focus:border-green-400"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="password">New Password</Label>
                                    <Input
                                        id="password"
                                        type="password"
                                        placeholder="Leave blank to keep current"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="bg-black/40 border-zinc-800 focus:border-green-400"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end pt-4">
                                <Button
                                    type="submit"
                                    disabled={isLoading}
                                    className="bg-green-400 hover:bg-green-500 text-black font-bold rounded-full px-8 h-11"
                                >
                                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                                    Save Profile Changes
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                {/* Subscription & Requests Card */}
                <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm text-white">
                    <CardHeader>
                        <CardTitle className="text-2xl flex items-center gap-2">
                            <Zap className="w-6 h-6 text-amber-400" />
                            Plan & Usage
                        </CardTitle>
                        <CardDescription className="text-zinc-400">
                            Monitor your current subscription and request limits.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="p-6 rounded-xl border border-green-400/20 bg-green-400/5 flex flex-col md:flex-row items-center justify-between gap-4">
                            <div>
                                <p className="text-sm text-zinc-400 mb-1">Current Active Plan</p>
                                <p className="text-2xl font-bold text-green-400 uppercase">{user.subscription_plan || "Starter"}</p>
                                {user.subscription_status === "trial" && user.trial_end_date && (
                                    <div className="flex items-center gap-2 mt-2">
                                        <div className="h-1.5 w-24 bg-zinc-800 rounded-full overflow-hidden">
                                            <div 
                                                className="h-full bg-amber-400" 
                                                style={{ width: `${(trialDaysLeft(user.trial_end_date) / 14) * 100}%` }}
                                            />
                                        </div>
                                        <p className="text-xs text-amber-400">
                                            {trialDaysLeft(user.trial_end_date)} days left in trial
                                        </p>
                                    </div>
                                )}
                            </div>
                            <Button className="bg-green-400 hover:bg-green-500 text-black font-bold rounded-full px-8" asChild>
                                <a href="/pricing">Manage Subscription</a>
                            </Button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-1">
                                <p className="text-xs text-zinc-400 uppercase tracking-wider font-semibold">Free Requests</p>
                                <p className="text-2xl font-mono text-white">{user.trial_requests_remaining ?? 0}</p>
                                <p className="text-[10px] text-zinc-500 italic">Signup bonus requests</p>
                            </div>
                            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-1">
                                <p className="text-xs text-zinc-400 uppercase tracking-wider font-semibold">Package Requests</p>
                                <p className="text-2xl font-mono text-white">{(user.plan_requests_remaining ?? 0).toLocaleString()}</p>
                                <p className="text-[10px] text-zinc-500 italic">Remaining in current plan</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Notifications & Settings Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Notifications */}
                    <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm text-white">
                        <CardHeader>
                            <CardTitle className="text-xl flex items-center gap-2">
                                <Bell className="w-5 h-5 text-blue-400" />
                                Notifications
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                                <div className="space-y-0.5">
                                    <p className="font-medium">Email Updates</p>
                                    <p className="text-xs text-zinc-400">Get notified about project changes</p>
                                </div>
                                <Switch defaultChecked className="data-[state=checked]:bg-green-400" />
                            </div>
                            <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                                <div className="space-y-0.5">
                                    <p className="font-medium">Usage Alerts</p>
                                    <p className="text-xs text-zinc-400">Notify when requests are low</p>
                                </div>
                                <Switch defaultChecked className="data-[state=checked]:bg-green-400" />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Integrations */}
                    <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm text-white">
                        <CardHeader>
                            <CardTitle className="text-xl flex items-center gap-2">
                                <Globe className="w-5 h-5 text-purple-400" />
                                Integrations
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center font-bold text-xs">A</div>
                                    <div>
                                        <p className="font-medium">AutoCAD</p>
                                        <p className="text-xs text-zinc-400">Not connected</p>
                                    </div>
                                </div>
                                <Button variant="ghost" size="sm" className="text-green-400 hover:text-green-300 hover:bg-green-400/10">Connect</Button>
                            </div>
                            <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center font-bold text-xs">R</div>
                                    <div>
                                        <p className="font-medium">Revit</p>
                                        <p className="text-xs text-zinc-400">Not connected</p>
                                    </div>
                                </div>
                                <Button variant="ghost" size="sm" className="text-green-400 hover:text-green-300 hover:bg-green-400/10">Connect</Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Advanced Settings */}
                <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm text-white border-dashed">
                    <CardHeader>
                        <CardTitle className="text-xl flex items-center gap-2">
                            <Key className="w-5 h-5 text-zinc-400" />
                            Advanced Configuration
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <Button variant="outline" className="border-zinc-800 bg-transparent hover:bg-zinc-800 text-zinc-300 w-full h-12">
                                Export Data
                            </Button>
                            <Button variant="outline" className="border-zinc-800 bg-transparent hover:bg-zinc-800 text-zinc-300 w-full h-12">
                                Import Data
                            </Button>
                            <Button variant="outline" className="border-zinc-800 bg-transparent hover:bg-zinc-800 text-zinc-300 w-full h-12">
                                Manage API Keys
                            </Button>
                        </div>
                        <p className="text-center text-[10px] text-zinc-600 mt-6 uppercase tracking-widest">
                            Danger zone: Deleting your account is irreversible.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}