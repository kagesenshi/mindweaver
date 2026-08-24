/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React, { useEffect, useState } from 'react';
import { ArrowLeft, Shield, Calendar, ShieldCheck, ShieldAlert, Award, FileText, Copy, Check, Edit3 } from 'lucide-react';
import PageLayout from '../../components/PageLayout';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import { cn } from '../../utils/cn';

const KeyValueRow = ({ label, value }) => {
    if (!value) return null;
    return (
        <div className="flex flex-col sm:flex-row sm:items-center py-2.5 border-b border-slate-100 dark:border-slate-800/60 last:border-b-0 text-sm">
            <span className="sm:w-1/3 text-slate-400 font-medium">{label}</span>
            <span className="flex-1 font-mono break-all text-slate-700 dark:text-slate-300">{value}</span>
        </div>
    );
};

const ServiceView = ({
    darkMode,
    browsingCert,
    onBack,
    certsHook
}) => {
    const { decodeCert, fetchCerts } = certsHook;
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const loadDetails = async () => {
            setLoading(true);
            try {
                const data = await decodeCert(browsingCert.id);
                setDetails(data);
            } catch (err) {
                console.error("Failed to decode cert", err);
            } finally {
                setLoading(false);
            }
        };
        if (browsingCert) {
            loadDetails();
        }
    }, [browsingCert, decodeCert]);

    const handleCopy = () => {
        navigator.clipboard.writeText(browsingCert.certificate);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <button
                    onClick={onBack}
                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-500"
                    title="Back to list"
                >
                    <ArrowLeft size={20} />
                </button>
                <div className="flex-1">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <Shield className="text-blue-500" size={24} />
                        {browsingCert.title || browsingCert.name}
                    </h2>
                    <p className="text-xs text-slate-500 font-mono mt-0.5">Resource Name: {browsingCert.name}</p>
                </div>
                <button
                    onClick={() => setShowEditModal(true)}
                    className="mw-btn-secondary px-4 py-2.5 flex items-center gap-2 text-sm"
                >
                    <Edit3 size={16} />
                    EDIT CERTIFICATE
                </button>
            </div>

            {loading ? (
                <div className="flex items-center justify-center p-12 text-slate-500 font-medium">
                    <Shield className="animate-spin text-blue-500 mr-2" size={24} />
                    Decoding certificate details...
                </div>
            ) : details ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left & Middle Column: Decoded Info */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Status Card */}
                        <div className={cn(
                            "p-5 rounded-2xl border flex items-center gap-4 shadow-sm",
                            details.is_valid
                                ? "bg-emerald-500/5 border-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                : "bg-rose-500/5 border-rose-500/10 text-rose-600 dark:text-rose-400"
                        )}>
                            {details.is_valid ? <ShieldCheck size={36} /> : <ShieldAlert size={36} />}
                            <div>
                                <h3 className="font-bold text-base">
                                    Certificate is {details.is_valid ? 'Active & Valid' : 'Invalid / Expired'}
                                </h3>
                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                                    {details.is_valid ? 'This certificate is currently trusted by deployed services.' : 'Please update the certificate to prevent authentication issues.'}
                                </p>
                            </div>
                        </div>

                        {/* Subject Details */}
                        <div className="bg-white dark:bg-[#0c0e12] rounded-2xl border border-slate-100 dark:border-slate-800/80 p-6 shadow-sm">
                            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                                <Award className="text-blue-500" size={18} />
                                Subject (Owner)
                            </h3>
                            <div className="space-y-1">
                                <KeyValueRow label="Common Name (CN)" value={details.subject.commonName} />
                                <KeyValueRow label="Organization (O)" value={details.subject.organizationName} />
                                <KeyValueRow label="Organizational Unit (OU)" value={details.subject.organizationalUnitName} />
                                <KeyValueRow label="Country (C)" value={details.subject.countryName} />
                                <KeyValueRow label="State/Province (ST)" value={details.subject.stateOrProvinceName} />
                                <KeyValueRow label="Locality (L)" value={details.subject.localityName} />
                            </div>
                        </div>

                        {/* Issuer Details */}
                        <div className="bg-white dark:bg-[#0c0e12] rounded-2xl border border-slate-100 dark:border-slate-800/80 p-6 shadow-sm">
                            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                                <ShieldCheck className="text-emerald-500" size={18} />
                                Issuer (Authority)
                            </h3>
                            <div className="space-y-1">
                                <KeyValueRow label="Common Name (CN)" value={details.issuer.commonName} />
                                <KeyValueRow label="Organization (O)" value={details.issuer.organizationName} />
                                <KeyValueRow label="Organizational Unit (OU)" value={details.issuer.organizationalUnitName} />
                                <KeyValueRow label="Country (C)" value={details.issuer.countryName} />
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Validity & Technical Details */}
                    <div className="space-y-6">
                        {/* Validity Dates */}
                        <div className="bg-white dark:bg-[#0c0e12] rounded-2xl border border-slate-100 dark:border-slate-800/80 p-6 shadow-sm">
                            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                                <Calendar className="text-violet-500" size={18} />
                                Validity Period
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <span className="text-xs text-slate-400 font-medium uppercase block">Valid From</span>
                                    <span className="text-sm font-mono font-bold text-slate-700 dark:text-slate-300">
                                        {new Date(details.valid_from).toLocaleString()}
                                    </span>
                                </div>
                                <div className="border-t border-slate-100 dark:border-slate-800/60 pt-3">
                                    <span className="text-xs text-slate-400 font-medium uppercase block">Valid Until</span>
                                    <span className="text-sm font-mono font-bold text-slate-700 dark:text-slate-300">
                                        {new Date(details.valid_to).toLocaleString()}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Technical Specs */}
                        <div className="bg-white dark:bg-[#0c0e12] rounded-2xl border border-slate-100 dark:border-slate-800/80 p-6 shadow-sm">
                            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                                <FileText className="text-slate-500" size={18} />
                                Technical Details
                            </h3>
                            <div className="space-y-3 text-xs">
                                <div>
                                    <span className="text-slate-400 block mb-0.5">Serial Number</span>
                                    <span className="font-mono break-all text-slate-700 dark:text-slate-300 font-bold">{details.serial_number}</span>
                                </div>
                                <div className="border-t border-slate-100 dark:border-slate-800/60 pt-2.5">
                                    <span className="text-slate-400 block mb-0.5">Signature Algorithm</span>
                                    <span className="font-mono text-slate-700 dark:text-slate-300 font-bold">{details.signature_algorithm}</span>
                                </div>
                                <div className="border-t border-slate-100 dark:border-slate-800/60 pt-2.5">
                                    <span className="text-slate-400 block mb-0.5">Version</span>
                                    <span className="font-mono text-slate-700 dark:text-slate-300 font-bold">{details.version}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="p-8 border border-dashed rounded-2xl text-center text-slate-500">
                    Unable to decode certificate metadata.
                </div>
            )}

            {/* PEM Certificate Raw Content */}
            <div className="bg-white dark:bg-[#0c0e12] rounded-2xl border border-slate-100 dark:border-slate-800/80 p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <FileText className="text-blue-500" size={18} />
                        PEM Certificate Content
                    </h3>
                    <button
                        onClick={handleCopy}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500 flex items-center gap-1.5 text-xs font-bold"
                    >
                        {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                        {copied ? 'Copied!' : 'Copy PEM'}
                    </button>
                </div>
                <pre className="p-4 bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-900 rounded-xl overflow-x-auto text-xs font-mono text-slate-600 dark:text-slate-400 select-all select-text max-h-[300px]">
                    {browsingCert.certificate}
                </pre>
            </div>

            {/* Edit Modal */}
            <Modal
                isOpen={showEditModal}
                onClose={() => setShowEditModal(false)}
                title="Edit Trusted Certificate"
                darkMode={darkMode}
            >
                <DynamicForm
                    entityPath="/trusted_certs"
                    mode="edit"
                    darkMode={darkMode}
                    initialData={browsingCert}
                    onSuccess={() => {
                        fetchCerts();
                        setShowEditModal(false);
                        onBack();
                    }}
                    onCancel={() => setShowEditModal(false)}
                />
            </Modal>
        </div>
    );
};

export default ServiceView;
