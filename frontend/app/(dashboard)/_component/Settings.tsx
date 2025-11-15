import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

export default function Settings() {
    return (
        <div className="text-white flex flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">

            <div className="w-[80%] p-4 gap-8 flex flex-col">

                <h1 className="text-white font-bold">Settings</h1>
                <div className="flex flex-col gap-4">
                    <h1 className="text-white font-bold">Account</h1>
                    <span className="w-full grid grid-cols-3 gap-4">

                        <span className="flex flex-col gap-2">
                            <label htmlFor="name">Profile Name</label>
                            <Input
                                value=""
                                id="name"
                                placeholder="First Name"
                                autoComplete="off"
                                className="border-1 border-[#3F3F3F] bg-[#1F1F1F] p-5"
                            />

                            <label htmlFor="name">Password</label>
                            <Input
                                value=""
                                id="name"
                                placeholder="************"
                                autoComplete="off"
                                className="border-1 border-[#3F3F3F] bg-[#1F1F1F] p-5"
                            />
                        </span>
                        <span className="flex flex-col h-full justify-between gap-2">
                            <span className="flex flex-col gap-2">
                                <label htmlFor="name">Email</label>
                                <Input
                                    value=""
                                    id="name"
                                    placeholder="email address"
                                    autoComplete="off"
                                    className="border-1 border-[#3F3F3F] bg-[#1F1F1F] p-5"
                                />
                            </span>
                            <div>
                                <Button
                                    className="bg-black text-white px-16"
                                >
                                    Edit Password
                                </Button>
                            </div>
                        </span>

                        <span>
                        </span>

                    </span>
                </div>

                <div className="flex flex-col w-[50%] gap-2">
                    <h1 className="text-white font-bold">Notifications</h1>
                    <div className="bg-[#2F2F2F] flex py-2 px-4 rounded-[10px]">
                        <span className="">
                            <p className="font-semibold">Email Notifications</p>
                            <p>
                                Receive email notifications about project updates, comments, and other activities.
                            </p>
                        </span>
                        <span>
                            <Switch id="airplane-mode" />
                        </span>
                    </div>
                </div>

                <div className="flex flex-col w-[50%] gap-2">
                    <h1 className="text-white font-bold">Integrations</h1>
                    <div className="bg-[#2F2F2F] flex py-2 px-4 rounded-[10px] flex items-center">
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

                    <div className="grid grid-cols-2 gap-4">

                        <div className="bg-[#2F2F2F] flex py-2 px-4 rounded-[10px] flex items-center justify-between">
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

                        <div className="bg-[#2F2F2F] flex py-2 px-4 rounded-[10px] flex items-center">
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

                        <div className="bg-[#2F2F2F] flex py-2 px-4 rounded-[10px] flex items-center">
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
                    >
                        Save Changes
                    </Button>
                </div>


            </div>
        </div>

    )
}