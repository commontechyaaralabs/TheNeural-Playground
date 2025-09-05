'use client';

import Link from 'next/link';
import Header from '../../components/Header';

export default function AboutPage() {

  return (
    <div className="min-h-screen bg-[#1c1c1c] text-white">
      <Header />

      <main className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              <span className="text-white">About </span>
              <span className="text-[#dcfc84]">TheNeural Playground</span>
            </h1>
            <p className="text-xl text-[#dcfc84] max-w-2xl mx-auto">
              Empowering the next generation with AI and Machine Learning
            </p>
          </div>

          {/* Main Content */}
          <div className="space-y-8">
            {/* What We Do Section */}
            <div className="bg-[#1c1c1c] border-2 border-[#bc6cd3]/20 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-[#dcfc84] mb-4 flex items-center gap-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                What We Do
              </h2>
              <p className="text-white text-lg leading-relaxed">
                TheNeural Playground is an innovative educational platform designed to make Artificial Intelligence and Machine Learning accessible to students of all ages. We believe that understanding AI is not just about coding&mdash;it&apos;s about creativity, problem-solving, and preparing for the future.
              </p>
            </div>

            {/* Our Mission Section */}
            <div className="bg-[#1c1c1c] border-2 border-[#bc6cd3]/20 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-[#dcfc84] mb-4 flex items-center gap-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Our Mission
              </h2>
              <p className="text-white text-lg leading-relaxed">
                To democratize AI education by providing hands-on, interactive learning experiences that transform complex machine learning concepts into engaging, understandable projects. We want every student to feel confident in their ability to work with and understand AI technologies.
              </p>
            </div>

            {/* How It Works Section */}
            <div className="bg-[#1c1c1c] border-2 border-[#bc6cd3]/20 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-[#dcfc84] mb-4 flex items-center gap-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                How It Works
              </h2>
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="bg-[#dcfc84] text-[#1c1c1c] w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                    1
                  </div>
                  <div>
                    <h3 className="text-white font-semibold mb-1">Create & Train</h3>
                    <p className="text-white/80">Students create their own machine learning models by providing examples and training data. Our platform makes this process intuitive and visual.</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-4">
                  <div className="bg-[#dcfc84] text-[#1c1c1c] w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                    2
                  </div>
                  <div>
                    <h3 className="text-white font-semibold mb-1">Build & Create</h3>
                    <p className="text-white/80">Once trained, students can integrate their AI models into various platforms like Scratch, Python, and more to create interactive projects.</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-4">
                  <div className="bg-[#dcfc84] text-[#1c1c1c] w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                    3
                  </div>
                  <div>
                    <h3 className="text-white font-semibold mb-1">Learn & Explore</h3>
                    <p className="text-white/80">Students gain hands-on experience with real AI concepts while building projects that matter to them.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Key Features Section */}
            <div className="bg-[#1c1c1c] border-2 border-[#bc6cd3]/20 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-[#dcfc84] mb-4 flex items-center gap-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                Key Features
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#dcfc84] rounded-full"></div>
                  <span className="text-white">Interactive Text Recognition Training</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#dcfc84] rounded-full"></div>
                  <span className="text-white">Multi-Platform Integration</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#dcfc84] rounded-full"></div>
                  <span className="text-white">Visual Learning Interface</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#dcfc84] rounded-full"></div>
                  <span className="text-white">Project-Based Learning</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#dcfc84] rounded-full"></div>
                  <span className="text-white">Real-Time Model Training</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#dcfc84] rounded-full"></div>
                  <span className="text-white">Cross-Platform Compatibility</span>
                </div>
              </div>
            </div>

            {/* Why AI Education Section */}
            <div className="bg-[#1c1c1c] border-2 border-[#bc6cd3]/20 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-[#dcfc84] mb-4 flex items-center gap-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Why AI Education Matters
              </h2>
              <p className="text-white text-lg leading-relaxed mb-4">
                In today&apos;s rapidly evolving technological landscape, understanding AI is becoming as fundamental as reading and writing. Our platform prepares students for a future where AI will be integrated into every aspect of life and work.
              </p>
              <div className="grid md:grid-cols-2 gap-4 text-white/80">
                <div>• Develops critical thinking skills</div>
                <div>• Prepares for future careers</div>
                <div>• Fosters creativity and innovation</div>
                <div>• Builds digital literacy</div>
              </div>
            </div>

            {/* Get Started Section */}
            <div className="bg-[#1c1c1c] border-2 border-[#dcfc84]/20 rounded-lg p-6 text-center">
              <h2 className="text-2xl font-bold text-[#dcfc84] mb-4">Ready to Get Started?</h2>
              <p className="text-white mb-6">
                Join thousands of students already learning AI through TheNeural Playground
              </p>
              <Link 
                href="/projects"
                className="bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] px-8 py-3 rounded-lg font-medium transition-all duration-300 inline-block hover:scale-105"
              >
                Start Your AI Journey
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
