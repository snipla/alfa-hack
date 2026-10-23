<?php

namespace App\Filament\Customer\Resources\Requests\Pages;

use App\Filament\Customer\Resources\Requests\RequestResource;
use App\Models\Request;
use Filament\Panel;
use Filament\Resources\Pages\CreateRecord;
use Illuminate\Support\Facades\Auth;

class CreateRequest extends CreateRecord
{
    protected static string $resource = RequestResource::class;

    protected function mutateFormDataBeforeCreate(array $data): array
    {
        // Добавляем user_id текущего авторизованного пользователя
        $data['user_id'] = Auth::id();
        $data['status'] = Request::REQUEST_CREATED;
        return $data;
    }
}
