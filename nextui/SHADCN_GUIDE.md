# Shadcn/UI Complete Guide for AI Report Generator

## 🎨 What is Shadcn/UI?

Shadcn/UI is a collection of reusable components built using Radix UI and Tailwind CSS. It provides beautiful, accessible, and customizable components for modern web applications.

## 📦 Installed Components

### Core Components

- ✅ **Button** - Multiple variants (default, outline, ghost, etc.)
- ✅ **Card** - Container with header, content, footer
- ✅ **Input** - Form input fields
- ✅ **Badge** - Status indicators and labels
- ✅ **Progress** - Progress bars and loading indicators
- ✅ **Tabs** - Tab navigation system
- ✅ **Textarea** - Multi-line text input
- ✅ **Select** - Dropdown selection
- ✅ **Dialog** - Modal dialogs and popups
- ✅ **Alert** - Alert messages and notifications
- ✅ **Separator** - Visual dividers

### Available Radix UI Primitives

- `@radix-ui/react-slot` - Component composition
- `@radix-ui/react-progress` - Progress indicators
- `@radix-ui/react-tabs` - Tab navigation
- `@radix-ui/react-dialog` - Modal dialogs
- `@radix-ui/react-dropdown-menu` - Dropdown menus
- `@radix-ui/react-popover` - Popover components
- `@radix-ui/react-select` - Select dropdowns
- `@radix-ui/react-separator` - Visual separators
- `@radix-ui/react-toast` - Toast notifications
- `@radix-ui/react-accordion` - Collapsible content
- `@radix-ui/react-alert-dialog` - Alert dialogs
- `@radix-ui/react-avatar` - User avatars
- `@radix-ui/react-checkbox` - Checkboxes
- `@radix-ui/react-label` - Form labels
- `@radix-ui/react-scroll-area` - Custom scrollbars
- `@radix-ui/react-switch` - Toggle switches
- `@radix-ui/react-tooltip` - Tooltips
- `@radix-ui/react-hover-card` - Hover cards
- `@radix-ui/react-menubar` - Menu bars
- `@radix-ui/react-navigation-menu` - Navigation menus
- `@radix-ui/react-radio-group` - Radio button groups
- `@radix-ui/react-slider` - Range sliders

## 🚀 Usage Examples

### 1. Button Component

```jsx
import { Button } from "@/components/ui/button";

// Basic usage
<Button>Click me</Button>

// With variants
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>

// With sizes
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>

// With icons
<Button>
  <Plus className="h-4 w-4 mr-2" />
  Add Item
</Button>
```

### 2. Card Component

```jsx
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content goes here</p>
  </CardContent>
</Card>;
```

### 3. Dialog Component

```jsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>Dialog description</DialogDescription>
    </DialogHeader>
    <div>Dialog content</div>
  </DialogContent>
</Dialog>;
```

### 4. Select Component

```jsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select an option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>;
```

### 5. Alert Component

```jsx
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";

<Alert>
  <Info className="h-4 w-4" />
  <AlertDescription>This is an informational alert.</AlertDescription>
</Alert>;
```

## 🎨 Styling and Theming

### CSS Variables

The theme is controlled by CSS variables in `globals.css`:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222.2 84% 4.9%;
  --muted: 210 40% 96%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96%;
  --accent-foreground: 222.2 84% 4.9%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}
```

### Dark Mode

Dark mode is automatically supported through the `.dark` class:

```css
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... other dark mode variables */
}
```

## 🔧 Customization

### 1. Component Variants

Use `class-variance-authority` to create component variants:

```jsx
import { cva } from "class-variance-authority";

const buttonVariants = cva("base-styles", {
  variants: {
    variant: {
      default: "default-styles",
      outline: "outline-styles",
    },
    size: {
      default: "default-size",
      sm: "small-size",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
});
```

### 2. Utility Function

Use the `cn` utility for conditional classes:

```jsx
import { cn } from "@/lib/utils";

<div className={cn("base-classes", condition && "conditional-classes")} />;
```

## 📱 Responsive Design

All components are built with mobile-first responsive design:

```jsx
// Responsive grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

// Responsive text
<h1 className="text-2xl md:text-3xl lg:text-4xl">

// Responsive spacing
<div className="p-4 md:p-6 lg:p-8">
```

## ♿ Accessibility

Shadcn/UI components are built with accessibility in mind:

- **Keyboard Navigation** - All interactive elements are keyboard accessible
- **Screen Reader Support** - Proper ARIA labels and roles
- **Focus Management** - Visible focus indicators
- **Color Contrast** - Meets WCAG guidelines

## 🎯 Best Practices

### 1. Component Composition

```jsx
// Good: Compose components
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    <Button>Action</Button>
  </CardContent>
</Card>

// Avoid: Over-nesting
<div className="card">
  <div className="card-header">
    <h3>Title</h3>
  </div>
</div>
```

### 2. Consistent Spacing

```jsx
// Use consistent spacing scale
<div className="space-y-4">  // 1rem
<div className="space-y-6">  // 1.5rem
<div className="space-y-8">  // 2rem
```

### 3. Icon Usage

```jsx
import { Plus, Edit, Trash2 } from "lucide-react";

// Consistent icon sizing
<Plus className="h-4 w-4" />      // Small
<Plus className="h-5 w-5" />      // Medium
<Plus className="h-6 w-6" />      // Large
```

## 🚀 Advanced Features

### 1. Glass-morphism Effect

```jsx
<Card className="border-0 shadow-sm bg-white/60 backdrop-blur-sm">
  {/* Glass-morphism card */}
</Card>
```

### 2. Gradient Backgrounds

```jsx
<div className="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
  {/* Gradient background */}
</div>
```

### 3. Animation Classes

```jsx
<div className="transition-all hover:shadow-md">{/* Hover animation */}</div>
```

## 📚 Resources

- [Shadcn/UI Documentation](https://ui.shadcn.com/)
- [Radix UI Documentation](https://www.radix-ui.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)

## 🎨 Your Current Implementation

Your AI Report Generator now uses:

1. **Modern Dashboard** - Tabbed interface with glass-morphism
2. **Enhanced File Upload** - Drag & drop with progress tracking
3. **Template Selector** - Grid layout with filtering and search
4. **Unified Chat** - Professional chat interface
5. **Responsive Design** - Works on all screen sizes

The UI now looks like a premium, enterprise-grade application! 🎉
