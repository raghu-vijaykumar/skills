import React from 'react';

type Props = {
  x: number;
  y: number;
  color?: string;
  size?: number;
  label?: string;
  scale?: number;
};

export function LoadBalancer({x, y, color = '#a78bfa', size = 150, label = 'LOAD BALANCER', scale = 1}: Props) {
  return (
    <div style={{position: 'absolute', left: x, top: y, width: size + 40, textAlign: 'center', transform: `scale(${scale})`, transformOrigin: 'top left'}}>
      <svg width={size} height={size} viewBox="0 0 70 70">
        <circle cx="35" cy="36" r="29" fill="#0d1117" stroke={color} strokeWidth="2.5" />
        <path
          fill={color}
          d="M35,7.333C19.168,7.333,6.334,20.167,6.334,36c0,15.833,12.834,28.667,28.666,28.667
            c15.833,0,28.667-12.834,28.667-28.667C63.667,20.167,50.833,7.333,35,7.333z
            M53,27h-9v-1.791l-2.795,3.525l-1.285-1.816
            L27.236,35H38v-1.922l6,2.244V32h9v9h-9v-3.323l-6,2.245V38H27.238l12.799,8.081l1.168-1.878L44,47.791V46h9v9h-9v-3.598
            l-6.218-1.496l0.85-1.805L23,37.989V44H13V29h10v6.01l15.748-10.112l-0.965-1.804L44,21.597V18h9V27z"
        />
        <circle cx="35" cy="36" r="29" fill="none" stroke={`${color}44`} strokeWidth="1" />
      </svg>
      <div style={{marginTop: 2, fontSize: 14, fontWeight: 800, color: '#F0F6FC'}}>{label}</div>
    </div>
  );
}
