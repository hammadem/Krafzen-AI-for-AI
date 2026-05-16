// This contain data for static pages those are all across the webpage

// Static History Data Will be integrated with backend soon
// Removed as API integrated export const historyData: HistoryData[] = []

// Example Searches
export const examplePrompt: [string, string][] = [
  ["Draw a 12x10 kitchen", "with a door on the right"],
  ["Create a 15x12 bedroom", "with two windows and a door"],
  ["Draw a 10x8 bathroom", "with a door on left"],
  ["Draw a 12x10 garage", "with a large door in the middle"]
]

//Template details
export const TemplateData = {
  url: "/dashboard/tempexample.png",
  title: "Modern House",
  details: "A compact and efficient 2-bedroom modern house"
}

// FAQs Questions Data
export const faqs: FAQs[] = [
  {
    type: "General",
    QandA: [
      {
        question: "Q1. What is KRAFZEN AI?",
        answer: ["KRAFZEN AI is a SaaS platform that transforms natural voice or text instructions into accurate CAD/DXF/DWG/Revit/BIM MEP models and as-built/instrumentation drawings."]
      },
      {
        question: "Q2. Who can benefit from using KRAFZEN AI?",
        answer: ["Our platform is designed for MEP engineers, architects, contractors, designers, and facility managers who need faster, more accurate CAD and BIM drawings without manual drafting."],
      },
      {
        question: "Q3. Do I need prior CAD or BIM expertise to use it?",
        answer: ["No. KRAFZEN AI is built with a simple interface. Users can input instructions in plain text or voice, and the system auto-generates accurate technical drawings."]
      }
    ]
  },
  {
    type: "Features & Functionality",
    QandA: [
      {
        question: "Q1. What file formats does KRAFZEN AI support?",
        answer: ["You can export to DXF, DWG, Revit, and BIM formats. Enterprise plans also support custom exports."]
      },
      {
        question: "Q2. Can KRAFZEN AI handle complex MEP and instrumentation layouts?",
        answer: ["Yes. Our AI is optimized for MEP systems (HVAC, piping, ducts, electrical) and can also generate instrumentation and as-built drawings for industrial projects."]
      },
      {
        question: "Q3. Does it support collaboration?",
        answer: ["Yes. Team collaboration tools are available in the Professional and Enterprise plans, allowing multiple users to work on shared projects."]
      },
      {
        question: "Q4. Can I integrate KRAFZEN AI with existing tools like AutoCAD or Revit?",
        answer: ["Yes. The platform is designed to integrate smoothly with AutoCAD, Revit, and BIM 360 through direct exports and API access (available in higher plans)."]
      }
    ]
  },
  {
    type: "Pricing & Plans",
    QandA: [
      {
        question: "Q1. Is there a free plan?",
        answer: ["Yes. The Free Plan allows limited projects per month with basic exports (DXF/DWG). It’s a great way to test the platform before upgrading.",]
      },
      {
        question: "Q2. What’s the difference between Pro and Professional plans?",
        answer: ["Pro: Unlimited projects, exports to all formats (DXF, DWG, Revit, BIM), smart AI adjustments.", "Professional: Everything in Pro, plus advanced MEP drafting, instrumentation layouts, team workspaces, and API integrations."]
      },
      {
        question: "Q3. Do you offer annual billing discounts?",
        answer: ["Yes. Annual subscriptions offer up to 20% savings compared to monthly billing."]
      },
      {
        question: "Q4. What if my company needs more than what’s offered in Professional?",
        answer: ["Our Enterprise plan includes custom pricing, white-labeling, on-premise deployment, and dedicated support."
        ]
      }
    ]
  },
  {
    type: "Security & Data",
    QandA: [
      {
        question: "Q1. How secure is my data?",
        answer: ["We use AES-256 encryption for stored data, TLS 1.2+ for data in transit, and follow SOC 2 and ISO 27001 best practices. Your CAD files and project data remain secure at all times."]
      },
      {
        question: "Q2. Who owns the generated CAD/BIM files?",
        answer: ["You do. All deliverables generated through KRAFZEN AI belong to the client, as outlined in our IP Rights Agreement."]
      },
      {
        question: "Q3. Where is my data stored?",
        answer: ["Data is stored in secure, U.S.-based servers. Enterprise clients may request regional hosting or on-premise deployment."]
      }
    ]
  },
  {
    type: "Support & Onboarding",
    QandA: [
      {
        question: "Q1. How do I get started?",
        answer: ["Simply sign up for the Free Plan, upload or dictate your first instructions, and KRAFZEN AI will generate your initial CAD output within minutes."]
      },
      {
        question: "Q2. Do you offer training?",
        answer: ["Yes. We provide onboarding guides, video tutorials, and dedicated training for enterprise customers."]
      },
      {
        question: "Q3. What support options are available?",
        answer: ["Free & Pro plans: Email support", "Professional: Priority support", "Enterprise: 24/7 dedicated support with an account manager"]
      }
    ]
  }
]

// About Page Data Here
export const aboutData: AboutData[] = [
  {
    heading: "About Krafzen",
    p: [
      "Krafzen is an innovative engineering and design outsourcing company that combines the power of artificial intelligence with the creativity and precision of expert human teams. We specialize in delivering solutions that are not only affordable but also accurate, reliable, and faster than traditional approaches. Our services span a wide spectrum—from CAD drafting, Building Information Modeling (BIM), and structural detailing to oil & gas design, civil engineering, and emerging SaaS-driven workflows.",
      "At Krafzen, we believe that every project, whether it begins as a sketch, a scanned drawing, or just an idea, has the potential to become something extraordinary. By integrating automation with professional insight, we transform concepts into ready-to-use deliverables that meet industry standards and client expectations. More than just an outsourcing partner, we aim to be a strategic ally, helping organizations reduce costs, improve efficiency, and achieve excellence through a unique blend of technology and human intelligence."
    ]
  },
  {
    heading: "Mission",
    p: [
      "Our mission is to revolutionize the way engineering and design projects are executed. We are committed to empowering businesses by combining AI-driven automation with specialized expertise, ensuring that every project is carried out with unmatched precision, speed, and cost-effectiveness.",
      "We strive to create value for our clients by delivering solutions that simplify complex workflows, enhance collaboration, and drive innovation. Through a strong focus on quality, integrity, and reliability, Krafzen is dedicated to helping industries—from construction and oil & gas to civil and digital engineering—build better, faster, and smarter",
    ]
  },
  {
    heading: "Vision",
    p: [
      "Our vision is to redefine the future of engineering and design outsourcing by building a global ecosystem where technology and human creativity work seamlessly together. We aspire to set new industry benchmarks in efficiency, scalability, and innovation, creating solutions that not only solve today’s challenges but also anticipate the demands of tomorrow.",
      "Krafzen envisions a world where AI-enhanced engineering becomes the standard, enabling organizations across industries to unlock new levels of productivity, sustainability, and growth. By continually investing in cutting-edge technologies, nurturing skilled talent, and focusing on client success, we aim to become the trusted global leader in next-generation engineering solutions.",
    ]
  }
]

// Pricing Plans Data Here
// Pricing Plans Data Here
export const PricingPlans: PricingPlans = {
  monthly: [
    {
      type: "Starter",
      price: "$149",
      stripeLink: "https://buy.stripe.com/9B6cN53rB8FTgPL3HY4wM09",
      features: [
        "Includes 50 drawings per month",
        "15 free workspace requests when you sign up (no card)",
        "Up to 3 team seats",
        "Access to transcript view",
        "Built-in JSON editor",
        "DXF export support",
        "Email support included",
        "Unlimited Projects",
      ],
    },
    {
      type: "Professional",
      price: "$499",
      stripeLink: "https://buy.stripe.com/3cIeVdbY76xL6b7diy4wM0a",
      features: [
        "Includes 300 drawings per month",
        "15 free workspace requests when you sign up (no card)",
        "Up to 10 team seats",
        "Batch uploads for faster workflows",
        "Google Drive & Dropbox connectors",
        "Priority queue for faster processing",
        "Advanced export formats (including CSV)",
        "Unlimited projects",
      ],
    },
    {
      type: "Enterprise",
      price: "$1,499",
      stripeLink: "https://buy.stripe.com/bJebJ13rBf4heHDceu4wM0b",
      features: [
        "Includes 2,000 drawings per month",
        "15 free workspace requests when you sign up (no card)",
        "Up to 25 team seats",
        "API access & webhooks integration",
        "Single Sign-On (SSO) & role management",
        "Region pinning for data control",
        "White-label reports for branding",
        "Unlimited projects",
      ],
    },
    {
      type: "Enterprise Plus",
      price: "Custom",
      stripeLink: undefined, // Contact Us
      features: [
        "Includes custom request volume",
        "15 free workspace requests when you sign up (no card)",
        "25+ team seats",
        "Dedicated workers for faster performance",
        "Private storage for enhanced security",
        "Custom data retention options",
        "Quarterly model review with experts",
        "White-label reports for full branding control",
      ],
    },
  ],

  annual: [
    {
      type: "Starter",
      price: "$1,490",
      stripeLink: "https://buy.stripe.com/cNi7sL8LV7BP8jfemC4wM0c",
      features: [
        "Includes 50 drawings per month",
        "15 free workspace requests when you sign up (no card)",
        "Up to 3 team seats",
        "Access to transcript view",
        "Built-in JSON editor",
        "DXF export support",
        "Email support included",
        "Unlimited Projects",
      ],
    },
    {
      type: "Professional",
      price: "$4,990",
      stripeLink: "https://buy.stripe.com/00w3cvbY77BP42ZemC4wM0d",
      features: [
        "Includes 300 drawings per month",
        "15 free workspace requests when you sign up (no card)",
        "Up to 10 team seats",
        "Batch uploads for bulk workflows",
        "Google Drive & Dropbox connectors",
        "Priority queue for faster processing",
        "Advanced export formats (including CSV)",
        "Unlimited projects",
      ],
    },
    {
      type: "Enterprise",
      price: "$14,990",
      stripeLink: "https://buy.stripe.com/00w3cvd2b9JX6b7diy4wM0e",
      features: [
        "Includes 2,000 drawings per month",
        "15 free workspace requests when you sign up (no card)",
        "Up to 25 team seats",
        "API access & webhooks integration",
        "Single Sign-On (SSO) & role management",
        "Region pinning for data control",
        "White-label reports for branding",
        "Unlimited projects",
      ],
    },
    {
      type: "Enterprise Plus",
      price: "Custom",
      stripeLink: undefined, // Contact Us
      features: [
        "Includes custom request volume",
        "15 free workspace requests when you sign up (no card)",
        "25+ team seats",
        "Dedicated workers for faster performance",
        "Private storage for enhanced security",
        "Custom data retention options",
        "Quarterly model review with experts",
        "White-label reports for full branding control",
      ],
    },
  ],
};
