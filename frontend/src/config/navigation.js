import {
  BarChartIcon,
  BookOpenIcon,
  LayoutGridIcon,
  ScanIcon,
  TargetIcon,
  UserIcon,
} from '../components/icons.jsx'

// Main app navigation (Task 74). `task` names the frontend task that builds the
// real screen; until then the route shows a placeholder using `description`.
export const NAV_ITEMS = [
  {
    to: '/dashboard',
    label: 'Dashboard',
    icon: LayoutGridIcon,
    eyebrow: 'Overview',
  },
  {
    to: '/analyzer',
    label: 'Prompt Analyzer',
    icon: ScanIcon,
    eyebrow: 'Detection',
    summary: 'Classify a prompt and see why it was flagged.',
    description:
      'Paste a prompt to classify it as Safe, Direct Jailbreak or Indirect Injection, with a confidence score and the attack sub-type.',
    task: 'Task 75',
  },
  {
    to: '/simulation',
    label: 'Simulation Lab',
    icon: TargetIcon,
    eyebrow: 'Practice',
    summary: 'Practise against scripted attack scenarios.',
    description: 'Work through scripted attack scenarios and watch detection results update turn by turn.',
    task: 'Task 83',
  },
  {
    to: '/learning',
    label: 'Learning Hub',
    icon: BookOpenIcon,
    eyebrow: 'Learning',
    summary: 'Build safe-prompting skills step by step.',
    description: 'Tutorials on secure prompting, with progress tracking, XP and category filters.',
    task: 'Task 87',
  },
  {
    to: '/analytics',
    label: 'Analytics',
    icon: BarChartIcon,
    eyebrow: 'Insights',
    description: 'Attack frequency, model performance and a breakdown of detected attack sub-types.',
    task: 'Task 88',
  },
  {
    to: '/profile',
    label: 'Profile',
    icon: UserIcon,
    eyebrow: 'Account',
    description: 'Personal information, notification preferences and API key.',
    task: 'Task 92',
  },
]

export function findNavItem(path) {
  return NAV_ITEMS.find((item) => item.to === path)
}
