"use client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/context/AuthContext";
import { createClient } from "@/lib/supabase/supabaseClient";
import { useState } from "react";

export default function Settings() {
    const { user, setUser } = useAuth();
    const [editing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [details, setDetails] = useState({
        firstname: user?.firstname?.toString() ? user?.firstname?.toString() : "",
        email: user?.email?.toString() ? user?.email?.toString() : "",
        password: ""
    });

    const hasChanges = () => {
        return details?.email !== user?.email?.toString() && details?.email !== "" &&
            details?.firstname !== "" && details?.firstname !== user?.firstname?.toString()
            && details?.password !== "" ? false : true;
    }

    const handleSave = async () => {
        if (!hasChanges() || user === null) return;
        setLoading(true);
        const supabase = createClient();

        try {
            // ---------- UPDATE USER METADATA ----------
            if (details.firstname !== user.firstname) {
                const { error } = await supabase.auth.updateUser({
                    data: { firstname: details.firstname }
                });

                if (error) throw error;
            }

            // ---------- UPDATE USER EMAIL ----------
            if (details.email !== user.email) {
                const { error } = await supabase.auth.updateUser({
                    email: details.email
                });

                if (error) throw error;
            }

            // ---------- UPDATE USER PASSWORD ----------
            if (details.password.length > 0) {
                const { error } = await supabase.auth.updateUser({
                    password: details.password
                });

                if (error) throw error;
            }

            // Update React AuthContext user
            setUser({
                ...user,
                firstname: details.firstname,
                email: details.email
            });
            setIsEditing(false);
        } catch (err) {
            console.log(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="text-white flex flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">

            <div className="w-[80%] p-4 gap-8 flex flex-col">

                <h1 className="text-white font-bold">Settings</h1>
                <div className="flex flex-col gap-4">
                    <h1 className="text-white font-bold">Account</h1>
                    <span className="w-full grid grid-cols-1 md:grid-cols-3 gap-4">

                        <span className="flex flex-col gap-2">
                            <label htmlFor="name">Profile Name</label>
                            <Input
                                value={details?.firstname !== undefined || null ? details?.firstname?.toString() : ""}
                                id="name"
                                placeholder="First Name"
                                autoComplete="off"
                                className={!editing ? "border-1 border-[#3F3F3F] bg-[#1F1F1F] p-5" : "border-1 border-[#3F3F3F] bg-[#4F4F4F] p-5"}
                                readOnly={!editing}
                                onChange={(e) =>
                                    setDetails({
                                        ...details, firstname: e.target.value
                                    })}
                            />

                            <label htmlFor="name">Password</label>
                            <Input
                                value={editing ? details?.password : ""}
                                id="name"
                                placeholder="************"
                                autoComplete="off"
                                className={!editing ? "border-1 border-[#3F3F3F] bg-[#1F1F1F] p-5" : "border-1 border-[#3F3F3F] bg-[#4F4F4F] p-5"}
                                readOnly={!editing}
                                onChange={(e) =>
                                    setDetails({
                                        ...details, password: e.target.value
                                    })}
                            />
                        </span>
                        <span className="flex flex-col h-full justify-between gap-2">
                            <span className="flex flex-col gap-2">
                                <label htmlFor="name">Email</label>
                                <Input
                                    value={details?.email !== undefined || null ? details?.email?.toString() : ""}
                                    id="name"
                                    placeholder="email address"
                                    autoComplete="off"
                                    className={!editing ? "border-1 border-[#3F3F3F] bg-[#1F1F1F] p-5" : "border-1 border-[#3F3F3F] bg-[#4F4F4F] p-5"}
                                    readOnly={!editing}
                                    onChange={(e) =>
                                        setDetails({
                                            ...details, email: e.target.value
                                        })} />
                            </span>

                            <div>
                                {
                                    !editing
                                        ?
                                        <Button
                                            className="bg-black text-white px-16"
                                            onClick={() => setIsEditing(true)}
                                        >
                                            Edit Password
                                        </Button>
                                        :
                                        <span className="flex gap-4">
                                            <Button
                                                className="bg-black text-white px-16"
                                                onClick={() => setIsEditing(false)}
                                                disabled={loading}
                                            >
                                                Cancel
                                            </Button>
                                            <Button
                                                disabled={loading}
                                                className="bg-green-800 hover:bg-green-600 text-white px-16"
                                                onClick={handleSave}
                                            >
                                                {loading ? "Saving" : "Save"}
                                            </Button>
                                        </span>
                                }
                            </div>
                        </span>

                        <span>
                        </span>

                    </span>
                </div>

                <div className="flex flex-col md:w-[50%] gap-2">
                    <h1 className="text-white font-bold">Notifications</h1>
                    <div className="bg-[#2F2F2F] flex py-2 px-4 rounded-[10px]">
                        <span className="">
                            <p className="font-semibold">Email Notifications</p>
                            <p>
                                Receive email notifications about project updates, comments, and other activities.
                            </p>
                        </span>
                        <span>
                            <Switch id="notification-mode" />
                        </span>
                    </div>
                </div>

                <div className="flex flex-col md:w-[50%] gap-2">
                    <h1 className="text-white font-bold">Integrations</h1>
                    <div className="bg-[#2F2F2F] flex sm:flex-row flex-col py-2 px-4 rounded-[10px] flex items-center">
                        <span className="">
                            <p className="font-semibold">Connect to other Services</p>
                            <p>
                                Connect you Krafzen account with other services for seamless workflow.
                            </p>
                        </span>
                        <span>
                            <Button
                                className="bg-black text-white px-12"
                            >
                                Connect
                            </Button>
                        </span>
                    </div>
                </div>


                <div className="flex flex-col gap-2">
                    <h1 className="text-white font-bold">Advanced Settings</h1>

                    <div className="grid md:grid-cols-2 gap-4">

                        <div className="bg-[#2F2F2F] flex sm:flex-row flex-col py-2 px-4 rounded-[10px] items-center justify-between">
                            <span className="">
                                <p className="font-semibold">Export Settings</p>
                                <p>
                                    Export your current settings to a file.
                                </p>
                            </span>
                            <span>
                                <Button
                                    className="bg-black text-white px-12"
                                >
                                    Export
                                </Button>
                            </span>
                        </div>

                        <div className="bg-[#2F2F2F] flex sm:flex-row flex-col py-2 px-4 rounded-[10px] items-center">
                            <span className="">
                                <p className="font-semibold">Import Settings</p>
                                <p>
                                    Import settings from a previously exported file.
                                </p>
                            </span>
                            <span>
                                <Button
                                    className="bg-black text-white px-12"
                                >
                                    Import
                                </Button>
                            </span>
                        </div>

                        <div className="bg-[#2F2F2F] flex sm:flex-row flex-col py-2 px-4 rounded-[10px] items-center">
                            <span className="">
                                <p className="font-semibold">Developer API Keys</p>
                                <p>
                                    Manage your API keys for custom integrations.
                                </p>
                            </span>
                            <span>
                                <Button
                                    className="bg-black text-white px-12"
                                >
                                    Manage
                                </Button>
                            </span>
                        </div>

                        <div />
                    </div>

                </div>


                <div className="flex w-full items-end justify-end">
                    <Button
                        className="bg-black text-white px-12"
                        disabled={hasChanges()}
                    >
                        Save Changes
                    </Button>
                </div>


            </div>
        </div >

    )
}