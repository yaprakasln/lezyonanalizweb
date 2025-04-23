//
//  DermaaiApp.swift
//  Dermaai
//
//  Created by Yaprak on 18.03.2025.
//

import SwiftUI
import FirebaseCore
import FirebaseAuth
import FirebaseDatabase

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        FirebaseApp.configure()
        return true
    }
}

@main
struct DermaaiApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
