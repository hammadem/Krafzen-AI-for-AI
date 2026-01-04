"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/supabaseClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "react-toastify";
import { Loader2, Upload } from "lucide-react";
import NavHeader from "@/components/NavHeader";

export default function AccountPage() {
    const { user, setUser, loading: authLoading } = useAuth();
    const router = useRouter();
    const supabase = createClient();

    const [isLoading, setIsLoading] = useState(false);
    const [firstname, setFirstname] = useState("");
    const [lastname, setLastname] = useState("");
    const [avatarFile, setAvatarFile] = useState<File | null>(null);
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

    useEffect(() => {
        if (!authLoading && !user) {
            router.push("/login");
        }
        if (user) {
            setFirstname(user.firstname || "");
            setLastname(user.lastname || "");
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

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            let avatarUrl = user?.avatar_url;

            // 1. Upload Avatar if changed
            if (avatarFile && user?.userId) {
                const fileExt = avatarFile.name.split('.').pop();
                const filePath = `${user.userId}-${Math.random()}.${fileExt}`;

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

            // 2. Update User Metadata
            const { data, error } = await supabase.auth.updateUser({
                data: {
                    firstname,
                    lastname,
                    avatar_url: avatarUrl
                }
            });

            if (error) throw error;

            // 3. Update Local State via Context
            if (data.user && user) {
                setUser({
                    ...user,
                    firstname: data.user.user_metadata.firstname,
                    lastname: data.user.user_metadata.lastname,
                    avatar_url: data.user.user_metadata.avatar_url
                });
                toast.success("Profile updated successfully!");
            }

        } catch (error: unknown) {
            console.error(error);
            const errorMessage = error instanceof Error ? error.message : "Failed to update profile";
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
        <div className="min-h-screen bg-black text-white">
            <NavHeader currentNav="Account Settings" />

            <div className="max-w-3xl mx-auto px-4 py-12">
                <Card className="bg-zinc-900 border-zinc-800 text-white">
                    <CardHeader>
                        <CardTitle className="text-2xl">Profile Settings</CardTitle>
                        <CardDescription className="text-gray-400">
                            Update your personal information and subscription details.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleUpdateProfile} className="space-y-8">

                            {/* Avatar Section */}
                            <div className="flex flex-col md:flex-row items-center gap-6">
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
                                    <h3 className="font-medium">Profile Picture</h3>
                                    <p className="text-sm text-gray-400">
                                        JPG, GIF or PNG. Max size of 800K
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
                                        className="bg-black border-zinc-800 focus:border-green-400"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="lastname">Last Name</Label>
                                    <Input
                                        id="lastname"
                                        value={lastname}
                                        onChange={(e) => setLastname(e.target.value)}
                                        className="bg-black border-zinc-800 focus:border-green-400"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    value={user.email}
                                    disabled
                                    className="bg-zinc-950 border-zinc-800 text-gray-400 cursor-not-allowed"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label>Subscription Plan</Label>
                                <div className="p-4 rounded-lg border border-green-400/20 bg-green-400/5 flex items-center justify-between">
                                    <div>
                                        <p className="font-semibold text-green-400">{user.subscription_plan || "Free Trial"}</p>
                                        <p className="text-xs text-gray-400">Current active plan</p>
                                    </div>
                                    <Button variant="outline" className="border-green-400 text-green-400 hover:bg-green-400 hover:text-black" asChild>
                                        <a href="/pricing">Upgrade</a>
                                    </Button>
                                </div>
                            </div>

                            <div className="flex justify-end pt-4">
                                <Button
                                    type="submit"
                                    disabled={isLoading}
                                    className="bg-green-400 hover:bg-green-500 text-black font-bold rounded-full px-8"
                                >
                                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                                    Save Changes
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
