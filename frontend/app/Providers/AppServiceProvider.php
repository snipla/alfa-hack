<?php

namespace App\Providers;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\URL;
use Illuminate\Support\ServiceProvider;
use Livewire\Livewire;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        if (config('app.env') === 'local') { // можно ограничить только для локальной разработки
            URL::forceRootUrl(config('app.url'));
        }
//        Livewire::setScriptRoute(function ($handle, $path) {
//            dd($path);
//            return Route::get('/' . $path, $handle);
//        });
    }
}
