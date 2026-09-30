"use client";

import React, { useState, useEffect } from "react";

interface CrystalIntelligenceOrbProps {
  totalAlerts?: number;
  totalIncidents?: number;
  totalClusters?: number;
  actionableIncidents?: number;
  actionableCount?: number;
  className?: string;
}

export const CrystalIntelligenceOrb: React.FC<CrystalIntelligenceOrbProps> = ({
  totalAlerts = 3000,
  totalIncidents,
  totalClusters,
  actionableIncidents,
  actionableCount,
  className = "",
}) => {
  const resolvedIncidents = totalIncidents ?? totalClusters ?? 543;
  const resolvedActionable = actionableIncidents ?? actionableCount ?? 113;
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: x * 10, y: -y * 10 });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
    setIsHovered(false);
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={handleMouseLeave}
      style={{
        perspective: "1000px",
      }}
      className={`relative select-none flex items-center justify-center p-6 ${className}`}
    >
      {/* 3D Tilted Container */}
      <div
        style={{
          transform: `rotateY(${tilt.x}deg) rotateX(${tilt.y}deg)`,
          transition: isHovered ? "transform 0.15s ease-out" : "transform 0.7s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
        className="relative w-64 h-64 flex items-center justify-center"
      >
        {/* Ambient Specular Back-Glow */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-teal-500/10 via-amber-500/5 to-teal-400/15 blur-2xl pointer-events-none" />

        {/* Outer Ring: Telemetry Ingestion Layer */}
        <div className="absolute inset-2 rounded-full border border-ivory-300/60 shadow-xs animate-[spin_60s_linear_infinite]" />

        {/* Middle Ring: Semantic Graph Correlation */}
        <div
          style={{ transform: "rotateX(65deg) rotateZ(20deg)" }}
          className="absolute w-56 h-56 rounded-full border border-teal-600/30 border-dashed animate-[spin_40s_linear_infinite_reverse]"
        />

        {/* Inner Counter-Ring: Incident Synthesis */}
        <div
          style={{ transform: "rotateY(60deg) rotateZ(-30deg)" }}
          className="absolute w-44 h-44 rounded-full border border-amber-600/35 animate-[spin_30s_linear_infinite]"
        />

        {/* Central Crystalline Geometric Core (SVG) */}
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40 drop-shadow-md z-10 transition-transform duration-300"
          style={{
            transform: isHovered ? "scale(1.04)" : "scale(1)",
          }}
        >
          <defs>
            <linearGradient id="crystalFacetA" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.85" />
              <stop offset="100%" stopColor="#E6F4F1" stopOpacity="0.55" />
            </linearGradient>
            <linearGradient id="crystalFacetB" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#F5F2EB" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#D9ECE8" stopOpacity="0.45" />
            </linearGradient>
            <linearGradient id="crystalFacetC" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0D9488" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#FAF7F2" stopOpacity="0.75" />
            </linearGradient>
            <linearGradient id="crystalEdgeGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0D9488" stopOpacity="0.7" />
              <stop offset="50%" stopColor="#D97706" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#0D9488" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Outer Facets */}
          <polygon
            points="100,20 165,60 100,100"
            fill="url(#crystalFacetA)"
            stroke="url(#crystalEdgeGlow)"
            strokeWidth="1"
          />
          <polygon
            points="100,20 35,60 100,100"
            fill="url(#crystalFacetB)"
            stroke="url(#crystalEdgeGlow)"
            strokeWidth="1"
          />
          <polygon
            points="35,60 35,140 100,100"
            fill="url(#crystalFacetC)"
            stroke="url(#crystalEdgeGlow)"
            strokeWidth="1"
          />
          <polygon
            points="165,60 165,140 100,100"
            fill="url(#crystalFacetA)"
            stroke="url(#crystalEdgeGlow)"
            strokeWidth="1"
          />
          <polygon
            points="35,140 100,180 100,100"
            fill="url(#crystalFacetB)"
            stroke="url(#crystalEdgeGlow)"
            strokeWidth="1"
          />
          <polygon
            points="165,140 100,180 100,100"
            fill="url(#crystalFacetC)"
            stroke="url(#crystalEdgeGlow)"
            strokeWidth="1"
          />

          {/* Central Pulsating Nucleus */}
          <circle cx="100" cy="100" r="14" fill="#0D9488" fillOpacity="0.2" />
          <circle cx="100" cy="100" r="6" fill="#0D9488" className="animate-pulse" />
        </svg>

        {/* Ambient Orbiting Intelligence Particles */}
        <div className="absolute w-2 h-2 rounded-full bg-teal-600/70 blur-[0.5px] top-6 left-12 animate-[ping_4s_ease-in-out_infinite]" />
        <div className="absolute w-2 h-2 rounded-full bg-amber-600/70 blur-[0.5px] bottom-8 right-10 animate-[ping_5s_ease-in-out_infinite_1s]" />

        {/* Floating Mini Overlay Tag */}
        <div className="absolute -bottom-2 bg-white/90 backdrop-blur-md border border-ivory-300 px-3 py-1 rounded-full shadow-crystal text-[10px] font-mono text-graphite-700 tracking-wider font-semibold flex items-center gap-1.5 z-20">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-pulse" />
          <span>CRYSTAL INTEL CORE</span>
        </div>
      </div>
    </div>
  );
};
