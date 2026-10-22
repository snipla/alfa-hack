<?php

namespace App\Filament\Customer\Resources\Requests\Pages;

use App\Filament\Customer\Resources\Requests\RequestResource;
use Filament\Resources\Pages\CreateRecord;

class CreateRequest extends CreateRecord
{
    protected static string $resource = RequestResource::class;
}
